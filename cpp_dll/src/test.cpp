#include <array>
#include <asio.hpp>
#include <chrono>
#include <iostream>
#include <print>
#include <ranges>
#include <sstream>
#include <vector>

#include "icmp_header.hpp"
#include "ipv4_header.hpp"
#include "ping.hpp"

std::string ping(const std::string &dest, int count) {
  asio::io_context io_context;
  auto future = asio::co_spawn(io_context, async_ping<ipv4_header>(dest, count),
                               asio::use_future);
  io_context.run();
  if (future.wait_for(std::chrono::nanoseconds(0)) ==
      std::future_status::deferred) {
    return "Totally loss";
  }
  std::stringstream ss;
  for (const auto &[ipv4_hdr, icmp_hdr, length, elapsed] : future.get()) {
    if (!length) {
      ss << "Timeout\n";
    }
    ss << length - ipv4_hdr.header_length() << " bytes from "
       << ipv4_hdr.source_address()
       << " icmp_seq=" << icmp_hdr.sequence_number()
       << ", ttl=" << ipv4_hdr.time_to_live() << ", time="
       << std::chrono::duration_cast<std::chrono::milliseconds>(elapsed).count()
       << "ms\n";
  }
  std::string data = ss.str();
  if (data.empty()) {
    return "Totally lost";
  }
  return data;
}

std::string pingv6(const std::string &dest, int count) {
  asio::io_context io_context;
  auto future = asio::co_spawn(io_context, async_ping<ipv6_header>(dest, count),
                               asio::use_future);
  io_context.run();
  if (future.wait_for(std::chrono::nanoseconds(0)) ==
      std::future_status::deferred) {
    return "Totally loss";
  }
  std::stringstream ss;
  for (const auto &[_, icmp_hdr, length, elapsed] : future.get()) {
    if (!length) {
      ss << "Timeout\n";
    }
    ss << length << " bytes from " << dest
       << " icmp_seq=" << icmp_hdr.sequence_number() << ", time="
       << std::chrono::duration_cast<std::chrono::milliseconds>(elapsed).count()
       << "ms\n";
  }
  std::string data = ss.str();
  if (data.empty()) {
    return "Totally lost";
  }
  return data;
}

struct tracert_compose {
  int index;
  long long t1;
  long long t2;
  long long t3;
  std::string address;
};

std::vector<tracert_compose> tracert(const std::string &dest) {
  asio::ip::icmp::endpoint destination;
  {
    asio::io_context io_context;
    asio::ip::icmp::resolver resolver(io_context);
    destination = *resolver.resolve(asio::ip::icmp::v4(), dest, "").begin();
  }
  std::vector<tracert_compose> list;
  std::size_t valid_idx = 0;
  for (auto ttl : std::views::iota(1) | std::views::take(30)) {
    asio::io_context io_context;
    asio::ip::tcp::resolver resolver(io_context);
    auto future = asio::co_spawn(
        io_context, async_ping<ipv4_header>(dest, 3, ttl), asio::use_future);
    io_context.run();
    if (future.wait_for(std::chrono::nanoseconds(0)) ==
        std::future_status::deferred) {
      continue;
    }
    std::array<long long, 3> local_list;
    asio::ip::address address;
    std::size_t idx = 0;
    for (const auto &[ipv4_hdr, _1, length, elapsed] : future.get()) {
      if (address.is_unspecified() &&
          !ipv4_hdr.source_address().is_unspecified()) {
        address = ipv4_hdr.source_address();
      }
      local_list[idx++] =
          length
              ? std::chrono::duration_cast<std::chrono::milliseconds>(elapsed)
                    .count()
              : -1;
    }
    list.emplace_back(ttl, local_list[0], local_list[1], local_list[2],
                      address.to_string());
    if (!address.is_unspecified()) {
      valid_idx = ttl - 1;
    }
    if (address == destination.address() || ttl - valid_idx > 3) {
      break;
    }
  }
  return list;
}

int main() {
  // std::cout << ping("www.baidu.com", 4) << '\n';
  // try {
  //     std::cout << pingv6("::1", 4) << '\n';
  // } catch (const std::exception& e) {
  //     std::cerr << e.what() << '\n';
  // }
  for (auto &[idx, t1, t2, t3, address] : tracert("qqof.net")) {
    std::println("{} {}ms {}ms {}ms {}", idx, t1, t2, t3, address);
  }
}
