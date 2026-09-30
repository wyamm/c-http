#include <iostream>
#include <vector>
#include <algorithm>
#include <ws2tcpip.h>
#include <winsock2.h>
#include <unistd.h>
#include <string>
#include <sstream>
#include <thread>
#include <fstream>

#include "parser.h"

auto format_body(std::string buf, std::string content_type) -> std::string;
auto handle_client(int client_socket) -> void;
auto read_http_request(int client_socket) -> ps::Parser;
auto read_from_file(std::string filename) -> std::string;
auto construct_filename(std::vector<std::string> vec) -> std::string;
auto handle_get(std::vector<std::string> &request_line, ps::Parser &parser) -> std::string;
auto handle_post(std::vector<std::string> &request_line, ps::Parser &parser) -> void;


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
    hints.ai_flags = AI_PASSIVE;

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
    freeaddrinfo(servinfo);
    return 0;
}

auto format_body(std::string buf, std::string content_type) -> std::string {
    auto ret = std::string("HTTP/1.1 200 OK\r\nContent-Type: " + content_type + "\r\nContent-Length: "
        + std::to_string(buf.size()) + "\r\n\r\n" + buf

    );
    return ret;
}

auto handle_client(int client_socket) -> void {
    std::string message;
    try {
        // RESPONDING
        auto parser = read_http_request(client_socket);
        if (parser.get_method().empty()) {
            closesocket(client_socket);
            return;
        }

        // the first element will be empty
        auto request_line = ps::split(parser.get_request_target(), std::string("/"));
        auto method = parser.get_method();
        if (method == "GET") {
            message = handle_get(request_line, parser);
        } else if (method == "POST") {
            handle_post(request_line, parser);
            message = std::string("HTTP/1.1 201 Created\r\n\r\n");
        }
        else {
            throw std::runtime_error("Invalid method\n");
        }

    } catch (const std::exception &e) {
        std::cerr << "Client handler error: " << e.what() << "\n";
        message = std::string("HTTP/1.1 404 Not Found\r\n\r\n");
    }


    try {
        auto sent = send(client_socket, message.data(), message.size(), 0);

        if (sent == SOCKET_ERROR) {
            throw std::runtime_error(":");

        }
    } catch (const std::runtime_error &e) {
        std::cerr << "send failed: " << e.what() << "\n";
    }
    closesocket(client_socket);
}

auto read_http_request(int client_socket) -> ps::Parser {
    auto data = std::string();
    auto buffer = std::vector<char>(1024);
    size_t header_end;
    // this recieves all of the headers and request line
    auto recieved = 0;
    // TODO: this is currently O(n^2), can we make it better?
    while ((header_end = data.find("\r\n\r\n")) == std::string::npos) {
        recieved = recv(client_socket, buffer.data(), buffer.size(), 0);
        if (recieved <= 0) {
            closesocket(client_socket);
            return {data};;
        }
        data.append(buffer.data(), recieved);
    }

    auto parser = ps::Parser(data.substr(0, header_end));
    auto body = data.substr(header_end + 4);
    // handle body later
    while (body.size() < parser.get_content_length()) {
        recieved = recv(client_socket, buffer.data(), buffer.size(), 0);
        body.append(buffer.data(), recieved);
    }

    if (body.size() > 0) {
        parser.set_body(body);
    }
    return parser;
}

auto construct_filename(std::vector<std::string> vec) -> std::string {
    auto start = vec.begin() + 2;
    auto ret = std::string();
    while (start != vec.end()) {
        ret += *start + "/";
        start++;
    }
    ret.pop_back();
    return ret;
}

auto read_from_file(std::string filename) -> std::string {
    auto infile = std::ifstream(filename, std::ios::binary);

    if (!infile.is_open()) {
        throw std::runtime_error("Could not open file: " + filename);
    }

    auto ret = std::string();
    auto buffer = std::vector<char>(4096);

    while (infile.read(buffer.data(), buffer.size()) || infile.gcount()) {
        ret.append(buffer.data(), infile.gcount());
    }

    return ret;

}

auto handle_get(std::vector<std::string> &request_line, ps::Parser &parser) -> std::string {
    auto message = std::string();
    try {
        if (request_line[1].empty()) {
            message = std::string("HTTP/1.1 200 OK\r\n\r\n");

        } else if (request_line[1] == "echo") {
            if (request_line.size() < 3) {
                throw std::runtime_error("Invalid path\n");
            }
            message = format_body(request_line[2], "text/plain");

        } else if (request_line[1] == "user-agent") {
            message = format_body(parser.get_user_agent(), "text/plain");
        } else if (request_line[1] == "files") {
            if (request_line.size() < 3) {
                throw std::runtime_error("Invalid path\n");
            }
            auto filename = construct_filename(request_line);
            auto content = read_from_file(filename);
            message = format_body(content, "application/octet-stream");
        }
    } catch (const std::exception &e) {
        throw std::runtime_error("GET: " + e.what());
    }


    return message;
}

auto handle_post(std::vector<std::string> &request_line, ps::Parser &parser) -> void {
    auto message = std::string();
    if (request_line.size() < 2) {
        throw std::runtime_error("Invalid request\n");
    }

    if (request_line[1] == "files") {
        if (request_line.size() < 3 || request_line.at(2).empty()) {
            throw std::runtime_error("Invalid filename\n");
        }
    }

    auto outfile = std::ofstream(request_line[2]);
    outfile << parser.get_body() << std::endl;
    outfile.close();
}
