#ifndef TCPING_HPP
#define TCPING_HPP

#include <asio.hpp>
#include <asio/experimental/awaitable_operators.hpp>
#include <chrono>
#include <cstdint>
#include <expected>
#include <string>
#include <system_error>
#include <type_traits>

namespace net {

asio::awaitable<std::expected<std::chrono::steady_clock::duration, std::string>>
async_tcping(std::string_view host, std::uint16_t port) {
  using namespace asio::experimental::awaitable_operators;

  auto executor = co_await asio::this_coro::executor;
  asio::ip::tcp::resolver resolver(executor);
  asio::ip::tcp::socket socket(executor);

  try {
    auto port_str = std::to_string(port);
    auto endpoint = *resolver.resolve(host, port_str).begin();
    auto start = std::chrono::steady_clock::now();
    co_await socket.async_connect(endpoint, asio::use_awaitable);
    auto end = std::chrono::steady_clock::now();
    std::error_code ec;
    socket.close(ec);
    co_return (end - start);

  } catch (const std::system_error &e) {
    co_return std::unexpected(e.code().message());

  } catch (const std::exception &e) {
    co_return std::unexpected(std::string(e.what()));

  } catch (...) {
    co_return std::unexpected(std::string());
  }
}

} // namespace net

#endif // TCPING_HPP
