from contextlib import asynccontextmanager

from fastapi import FastAPI
import asyncio
from concurrent.futures import ProcessPoolExecutor, as_completed
import pyautogui as pyauto
import cv2 as cv
import traceback
from matplotlib import pyplot as plt
import sys
import numpy as np
import time
from datetime import datetime

from classes import Bookie, EventConfigs
import database.db as db
from image_process import process_single, clean_ocr
from arb_calc import find_best_odds
from helpers import build_books, text_to_odds, screen_shot

async def capture_loop(app: FastAPI):
    books = app.state.books
    team = app.state.team
    abrv = app.state.abrv
    num_odds = app.state.num_odds
    executor = app.state.executor
    game_name = app.state.game_name
    # this gets the current running event loop
    # a single threaded loop that manages all my concurrent tasks - capture loop, incoming API request, database queries etc
    # this gives me a reference to the loop so i can schedule work to it
    event_loop = asyncio.get_event_loop()

    while True:
        try:
            full = await asyncio.to_thread(screen_shot) # to_thread starts another thread to take screen shot, so it doesn't block the whole thread. IO bound
            full = cv.cvtColor(np.array(full), cv.COLOR_RGB2BGR) # convert PIL obkect into IMG object
            book_list = list(books.items())
            timestamp = int(time.time())
            tasks = [
                # run_in_executor submits a job to the existing executor
                # executors picks up the work and returns awaitable
                event_loop.run_in_executor(executor, process_single, i, book.name, full)
                for i, book in book_list
            ]
            # run the await objects in sequence concurrently
            # gather doesn't run anything, it just tells the event loop "don't continue past this point until all the tasks have finished"
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for (i, book), result in zip(book_list, results):
                if isinstance(result, BaseException):
                    print(f"OCR error for {book.name}: {result}")
                    book.odds = [0.0] * num_odds
                    continue

                text = clean_ocr(result)
                odds = text_to_odds(book.name, text, team, abrv, num_odds)
                book.odds = odds if odds else [0.0] * num_odds

            margin, selected_bookies = find_best_odds(books, num_odds)

            app.state.latest = {
                "timestamp": timestamp,
                "margin": margin,
                "odds": {book.name: book.odds for _, book in books.items()},
                "selected_odds": [(b.name, b.odds) for b in selected_bookies]
            }

            # save the snap shot, save the margin snap shot too
            for book in books.values():
                book_id = app.state.name_to_id[book.name]
                outcomes = {o : book.odds[i] for i, o in enumerate(app.state.outcomes)}
                db.save_odds_snapshot(book_id, game_name, app.state.market, outcomes, datetime.now())

            db.save_margin_snapshot(game_name, margin,app.state.latest["selected_odds"])

        except Exception as e:
            print(f"Capture error: {e}")
        await asyncio.sleep(0.5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # start up
    """everything before yield will run on server start up"""
    # load bookies
    app.state.books = build_books("websites.txt")

    app.state.name_to_id = {book.name: db.get_bookie_id(book.name) for book in app.state.books.values()}
    # create process pool for OCR work
    app.state.executor = ProcessPoolExecutor(max_workers=(len(app.state.books)))

    # shared state for the latest results
    app.state.latest = {}

    app.state.task = None

    yield

    task: asyncio.Task | None = app.state.task
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    app.state.executor.shutdown(wait=True, cancel_futures=True)

    print("sucessfully cancelled")

    """everything after yield will run on server shut down"""

app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    print("hello")

# Booki getters
@app.get("/load_all_bookies")
def load_all_bookies() -> list[Bookie]:
    return db.load_all_bookie()

@app.get("/load_bookie")
def load_bookie(name: str) -> Bookie:
    return db.load_bookie(name)

# Bookie setters
@app.put("/save_bookie")
def save_bookies(bookie: Bookie):
    db.save_bookie(bookie)

@app.post("/start")
async def start_capture(config: EventConfigs):
    app.state.team = config.team
    app.state.abrv = config.abrv
    app.state.market = config.market
    app.state.game_name = config.game_name
    app.state.outcomes = config.outcomes
    app.state.num_odds = len(config.outcomes)

    # starts a coroutine (an async function) to run the capture loop as a backgrtound task
    # so this gets run along side HTTP request etc
    app.state.task = asyncio.create_task(capture_loop(app))
    return {"status": "started"}

@app.post("/stop")
async def stop_capture():
    if app.state.task is None:
        return {"error": "not running"}
    app.state.task.cancel()
    try:
        await app.state.task
    except asyncio.CancelledError:
        pass

    app.state.task = None
    return {"status": "stopped"}