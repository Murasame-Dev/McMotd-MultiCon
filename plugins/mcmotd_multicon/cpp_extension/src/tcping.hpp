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

asio::awaitable<std::chrono::milliseconds>
async_tcping(std::string_view host, std::uint16_t port, const std::chrono::steady_clock::duration& timeout) {
  using namespace asio::experimental::awaitable_operators;

  auto executor = co_await asio::this_coro::executor;
  asio::ip::tcp::resolver resolver(executor);
  asio::ip::tcp::socket socket(executor);

  auto port_str = std::to_string(port);
  auto endpoint = *resolver.resolve(host, port_str).begin();
  asio::steady_timer timer(executor);
  timer.expires_after(timeout);
  auto start = std::chrono::steady_clock::now();
  auto res = co_await (socket.async_connect(endpoint, asio::use_awaitable) || timer.async_wait(asio::use_awaitable));
  auto end = std::chrono::steady_clock::now();
  if (res.index()){
    throw std::system_error(std::make_error_code(std::errc::timed_out));
  }
  std::error_code ec;
  socket.close(ec);
  co_return std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
}

} // namespace net

#endif // TCPING_HPP
