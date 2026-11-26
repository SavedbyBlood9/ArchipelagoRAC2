// SPDX-License-Identifier: MIT
// The few socket calls the bridge and its test need, on Winsock (Windows) and POSIX (Linux, macOS,
// Android). Writes never raise SIGPIPE: a sidecar that goes away must not take the game with it.
#pragma once
#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
#else
#include <arpa/inet.h>
#include <cerrno>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
#endif
#include <cstddef>

namespace rac2ap::net {
#ifdef _WIN32
using socket_t = SOCKET;
using socklen = int;
constexpr socket_t invalid = INVALID_SOCKET;
inline bool startup() { WSADATA data{}; return WSAStartup(MAKEWORD(2, 2), &data) == 0; }
inline void cleanup() { WSACleanup(); }
inline void close(socket_t s) { closesocket(s); }
inline bool set_nonblocking(socket_t s) { u_long one = 1; return ioctlsocket(s, FIONBIO, &one) == 0; }
// The last call would have blocked (or, after connect, is still connecting).
inline bool would_block() { return WSAGetLastError() == WSAEWOULDBLOCK; }
inline bool connecting() { return would_block(); }
inline int nfds(socket_t) { return 0; }
inline void set_recv_timeout_ms(socket_t s, unsigned ms) {
    DWORD t = ms;
    setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, reinterpret_cast<const char*>(&t), sizeof t);
}
inline int send(socket_t s, const char* data, std::size_t size) {
    return ::send(s, data, static_cast<int>(size), 0);
}
#else
using socket_t = int;
using socklen = socklen_t;
constexpr socket_t invalid = -1;
inline bool startup() { return true; }
inline void cleanup() {}
inline void close(socket_t s) { ::close(s); }
inline bool set_nonblocking(socket_t s) {
    const int flags = fcntl(s, F_GETFL, 0);
#ifdef SO_NOSIGPIPE
    int one = 1;
    setsockopt(s, SOL_SOCKET, SO_NOSIGPIPE, &one, sizeof one); // macOS: no MSG_NOSIGNAL
#endif
    return flags >= 0 && fcntl(s, F_SETFL, flags | O_NONBLOCK) == 0;
}
inline bool would_block() { return errno == EAGAIN || errno == EWOULDBLOCK; }
inline bool connecting() { return errno == EINPROGRESS || would_block(); }
inline int nfds(socket_t s) { return s + 1; }
inline void set_recv_timeout_ms(socket_t s, unsigned ms) {
    timeval t{static_cast<time_t>(ms / 1000), static_cast<suseconds_t>((ms % 1000) * 1000)};
    setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &t, sizeof t);
}
inline int send(socket_t s, const char* data, std::size_t size) {
#ifdef MSG_NOSIGNAL
    return static_cast<int>(::send(s, data, size, MSG_NOSIGNAL));
#else
    return static_cast<int>(::send(s, data, size, 0));
#endif
}
#endif
}
