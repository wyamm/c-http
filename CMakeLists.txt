cmake_minimum_required(VERSION 3.23)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
project(socket)

add_executable(server)

target_sources(server
    PRIVATE
    src/main.cpp
)

add_library(parser)

target_sources(parser
    PRIVATE
    src/parser.cpp

    PUBLIC
      FILE_SET HEADERS
      BASE_DIRS
        src
      FILES
        src/parser.h
)

target_compile_options(server PRIVATE -Wall -Wextra -Wpedantic -Wshadow -Werror -fexperimental-library)

target_link_libraries(server
    PRIVATE
    parser
    ws2_32 # mswsock wsock32
)
