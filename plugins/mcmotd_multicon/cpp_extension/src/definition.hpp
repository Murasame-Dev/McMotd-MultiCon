#ifndef DEFINITION_HPP
#define DEFINITION_HPP

namespace net {
struct use_ipv4_t {};
struct use_ipv6_t {};

inline constexpr use_ipv4_t use_ipv4;
inline constexpr use_ipv6_t use_ipv6;
} // namespace net

#endif // DEFINITION_HPP