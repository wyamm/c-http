#ifndef PARSER_H
#define PARSER_H

#include <string>
#include <vector>
#include <algorithm>
#include <sstream>
#include <set>
// purpose of this class is to have something that is able to hold information about the requst being sent
namespace ps {

auto const HOST_LEN = 6;
auto const UA_LEN = 12;
auto const ACCEPT_LEN = 8;
auto const CONTENT_T_LEN = 16;
auto const CONTENT_L_LEN = 16;

auto const METHODS = std::set<std::string>{std::string("GET"), std::string("HEAD"), std::string("OPTIONS"), std::string("TRACE"),
                                            std::string("PUT"), std::string("DELETE"), std::string("POST"), std::string("PATCH"), std::string("PATCH"), std::string("CONNECT")};
class Parser {
public:
    Parser(std::string buf);
    Parser(const Parser &other) = default;
    Parser(Parser &&other) = default;
    auto operator=(Parser &other) -> Parser& = default;
    auto operator=(Parser &&other) -> Parser& = default;

    auto get_body() const -> std::string;
    auto get_method() const -> std::string {
        return method_;
    }
    auto get_request_target() const -> std::string {
        return request_target_;
    }
    auto split_request_target() -> void;

    auto get_http_version() const -> std::string {
        return http_version_;
    }

    auto get_host_port_() const -> std::string {
        return host_port_;
    }

    auto get_user_agent() const -> std::string {
        return user_agent_;
    }

    auto get_accepts() const -> std::string  {
        return accepts_;
    }

    auto get_content_length() const -> size_t {
        return content_l_;
    }

    auto set_body(const std::string &body) -> void {
        body_ = std::move(body);
    }
private:
    auto parse(const std::string& buf) -> void;

    std::string method_;
    std::string request_target_;
    std::string http_version_;

    std::string host_port_;
    std::string user_agent_;
    std::string accepts_;
    size_t content_l_ = 0;
    std::string content_t_;

    std::string body_;
};

auto split(const std::string& buf, std::string del) -> std::vector<std::string>;

}



#endif