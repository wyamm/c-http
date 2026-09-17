#include <iostream>
#include <vector>
#include <algorithm>
#include <ws2tcpip.h>
#include <winsock2.h>
#include <unistd.h>
#include <string>
#include <sstream>
#include <thread>

#include "parser.h"

auto format_body(std::string buf) -> std::string;
auto handle_client(int client_socket) -> void;
auto read_http_request(int client_socket) -> std::string;

int main() {
    // start WSA
    WSADATA wsaData;
    auto wVersionRequested = MAKEWORD(2, 2);
    auto wsaerr = WSAStartup(wVersionRequested, &wsaData);

    if (wsaerr != 0) {
        std::cerr << "The Winsock dll not found!" << "\n";
        return 1;
    } else {
        std::cout << "Winsock dll found!\n";
    }

    auto port = "4221";
    struct addrinfo hints, *servinfo;
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = INADDR_ANY;

    getaddrinfo(NULL, port, &hints, &servinfo); // we use getaddrinfo here instead

    // create a new socket
    auto serverSocket = socket(servinfo->ai_family, servinfo->ai_socktype, servinfo->ai_protocol);
    if (serverSocket == INVALID_SOCKET) {
        std::cerr << "Error at socket(): " << WSAGetLastError() << "\n";
        WSACleanup();
        return 1;
    } else {
        std::cout << "socket() is ok!\n";
    }

    // because we are going to be restarting our server quite often
    // setsocketop lets us rebind to the same port even
    auto reuse = 1;
    if (setsockopt(serverSocket, SOL_SOCKET, SO_REUSEADDR,( const char*)&reuse, sizeof(reuse))) {
        std::cerr << "unable to rebind to the same port\n";
        WSACleanup();
        closesocket(serverSocket);
        return 1;
    }

    // now we must bind the socket to the servers IP address and a valid port.
    if (bind(serverSocket, servinfo->ai_addr, servinfo->ai_addrlen)) {
        std::cerr << "Failed to bind to port 5555: " << WSAGetLastError() << "\n";
        WSACleanup();
        closesocket(serverSocket);
        return 1;
    }

    // listening for connections
    auto connection_backlog = 5;
    if (listen(serverSocket, connection_backlog) != 0) {
        std::cerr << "listen failed\n";
        WSACleanup();
        closesocket(serverSocket);
        return 1;
    }

    while (true) {
        // accepting connections, this is blocking
        struct sockaddr client_adr;
        auto client_addr_len = sizeof(client_adr);
        auto client_socket = accept(serverSocket, &client_adr, (socklen_t*) &client_addr_len);

        if (client_socket == INVALID_SOCKET) {
            std::cerr << "Accept failed" << WSAGetLastError() << "\n";
            continue;
        }

        // handle_client(client_socket);
        std::thread(handle_client, client_socket).detach();
    }


    WSACleanup();
    closesocket(serverSocket);

    return 0;
}

auto format_body(std::string buf) -> std::string {
    auto ret = std::string("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: "
        + std::to_string(buf.size()) + "\r\n\r\n" + buf

    );
    return ret;
}

auto handle_client(int client_socket) -> void {
    try {
        // RESPONDING
        std::string buf = read_http_request(client_socket);
        if (buf.empty()) {
            closesocket(client_socket);
            return;
        }

        auto parser = ps::Parser(buf);
        // the first element will be empty
        auto request_line = ps::split(parser.get_request_target(), std::string("/"));

        std::string message;
        if (request_line[1].empty()) {
            message = std::string("HTTP/1.1 200 OK\r\n\r\n");

        } else if (request_line[1] == "echo") {
            if (request_line.size() < 3) {
                message = "HTTP/1.1 400 Bad Request\r\n\r\n";
            } else {
                message = format_body(request_line[2]);
            }
        } else if (request_line[1] == "user-agent") {
            message = format_body(parser.get_user_agent());
        } else {
            message = std::string("HTTP/1.1 404 Not Found\r\n\r\n");
        }

        auto sent = send(client_socket, message.data(), message.size(), 0);

        if (sent == SOCKET_ERROR) {
            std::cerr << "send failed: " << WSAGetLastError() << "\n";

        }
    } catch (const std::exception &e) {
        std::cerr << "Client handler error: " << WSAGetLastError() << "\n";
    } catch(...) {
        std::cerr << "Unknown error\n";
    }

    closesocket(client_socket);
}

auto read_http_request(int client_socket) -> std::string {
    auto data = std::string();
    auto buffer = std::vector<char>(1024);

    // this recieves all of the headers and request line
    while (data.find("\r\n\r\n") == std::string::npos) {
        auto recieved = recv(client_socket, buffer.data(), buffer.size(), 0);
        if (recieved <= 0) {
            closesocket(client_socket);
            return data;
        }
        data.append(buffer.data(), recieved);
    }

    // handle body later
    return data;
}