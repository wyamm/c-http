#include "parser.h"
#include <iostream>

ps::Parser::Parser(std::string buf) {
    // maybe first split by "\r\n" and then remove space, and then split by respective delimiter
    /*

    / Request line
    GET                          // HTTP method
    /index.html                  // Request target
    HTTP/1.1                     // HTTP version
    \r\n                         // CRLF that marks the end of the request line

    / Headers
    Host: localhost:4221\r\n     // Header that specifies the server's host and port
    User-Agent: curl/7.64.1\r\n  // Header that describes the client's user agent
    Accept:\r\n              // Header that specifies which media types the client can accept
    \r\n                         // CRLF that marks the end of the headers

    / Request body (empty)
    */

    auto lines = split(buf, std::string("\r\n"));
    for (auto line : lines) {
        parse(line);
    }
}
auto ps::split(const std::string& buf, std::string del) -> std::vector<std::string> {
    size_t start = 0;
    size_t end = buf.find(del);
    auto ret = std::vector<std::string>();
    while (end != std::string::npos) {
        ret.emplace_back(buf.substr(start, end - start));
        start = end + del.length();
        end = buf.find(del, start);
    }

    ret.push_back(buf.substr(start));
    return ret;
}

auto ps::Parser::parse(const std::string& buf) -> void {
    auto token = std::string();
    for (auto c : buf) {
        token += c;
        if (token == std::string("Host")) {
            host_port_ = buf.substr(HOST_LEN);
            break;
        } else if (token == std::string("User-Agent")) {
            user_agent_ = buf.substr(UA_LEN);
            break;
        } else if (token == std::string("Accept")) {
            accepts_ = buf.substr(ACCEPT_LEN);
            break;
        } else if (ps::METHODS.contains(token)) {
            auto request_line = split(buf, std::string(" "));
            method_ = request_line[0];
            request_target_ = request_line[1];
            http_version_ = request_line[2];

            break;
        } else if (token == "Content-Length: ") {
            auto stream = std::stringstream(buf.substr(CONTENT_L_LEN));
            stream >> content_l_;
            break;
        } else if (token == "Content-Type: ") {
            content_t_ = buf.substr(CONTENT_T_LEN);
            break;
        }
    }

}