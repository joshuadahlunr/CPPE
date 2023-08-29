#ifndef __CPPE_UFCS_HPP__
#define __CPPE_UFCS_HPP__

#include <utility>
#include <type_traits>

#if defined(_MSC_VER) && !defined(__clang_major__)
	#ifndef ALWAYS_INLINE
		#define ALWAYS_INLINE __forceinline
	#endif
	#define ALWAYS_INLINE_LAMBDA [[msvc::forceinline]]
#else
	#ifndef ALWAYS_INLINE
		#define ALWAYS_INLINE __attribute__((always_inline))
	#endif
	#define ALWAYS_INLINE_LAMBDA __attribute__((always_inline))
#endif

#define CPPE_STRINGIFY_IMPL(s) #s
#define CPPE_STRINGIFY(s) CPPE_STRINGIFY_IMPL(s)

#define CPPE_FORWARD(x) std::forward<decltype(x)>(x)


// #define CPPE_UFCS(...) CPPE_GET_UFCS_MACRO(__VA_ARGS__, CPPE_UFCS_FUNCTION, CPPE_UFCS_PROPERTY)(__VA_ARGS__)

// #define CPPE_GET_UFCS_MACRO(_1, _2, _3, NAME, ...) NAME

#define CPPE_UFCS_PROPERTY(PROPNAME, OBJECT)\
[&] (auto&& obj) ALWAYS_INLINE_LAMBDA -> decltype(auto) {\
	if constexpr (requires{ CPPE_FORWARD(obj).PROPNAME; }) {\
		if constexpr (std::is_const_v<std::remove_reference_t<decltype(obj)>>\
		  && std::is_volatile_v<std::remove_reference_t<decltype(obj)>>)\
		    return std::forward<std::add_lvalue_reference_t<std::add_cv_t<decltype(CPPE_FORWARD(obj).PROPNAME)>>>(CPPE_FORWARD(obj).PROPNAME);\
		else if constexpr (std::is_const_v<std::remove_reference_t<decltype(obj)>>)\
			return std::forward<std::add_lvalue_reference_t<std::add_const_t<decltype(CPPE_FORWARD(obj).PROPNAME)>>>(CPPE_FORWARD(obj).PROPNAME);\
		else if constexpr (std::is_volatile_v<std::remove_reference_t<decltype(obj)>>)\
			return std::forward<std::add_lvalue_reference_t<std::add_volatile_t<decltype(CPPE_FORWARD(obj).PROPNAME)>>>(CPPE_FORWARD(obj).PROPNAME);\
		else return std::forward<std::add_lvalue_reference_t<decltype(CPPE_FORWARD(obj).PROPNAME)>>(CPPE_FORWARD(obj).PROPNAME);\
	/*NOTE: We don't use std::invoke since we would need to get a pointer to PROPNAME which is more work...*/\
	} else if constexpr (requires{ CPPE_FORWARD(obj).PROPNAME(); })\
		return CPPE_FORWARD(obj).PROPNAME();\
	else if constexpr (requires{ PROPNAME(CPPE_FORWARD(obj)); })\
		return PROPNAME(CPPE_FORWARD(obj));\
	else if constexpr (requires{ CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(PROPNAME)); })\
		return CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(PROPNAME));\
	else if constexpr (requires{ CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(PROPNAME)); })\
		return CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(PROPNAME));\
	else throw "failure!";\
	/*else static_assert(false, "Failed to find property or field `" CPPE_STRINGIFY(PROPNAME) "` on `" CPPE_STRINGIFY(OBJECT) "`");*/\
}(OBJECT)

#define CPPE_UFCS_FUNCTION(FUNCNAME, OBJECT, ...)\
[&] (auto&& obj, auto&& ...params) ALWAYS_INLINE_LAMBDA -> decltype(auto) {\
	if constexpr (requires{ CPPE_FORWARD(obj).FUNCNAME(CPPE_FORWARD(params)...); })\
		return CPPE_FORWARD(obj).FUNCNAME(CPPE_FORWARD(params)...);\
	else if constexpr (requires{ FUNCNAME(CPPE_FORWARD(obj), CPPE_FORWARD(params)...); })\
		return FUNCNAME(CPPE_FORWARD(obj), CPPE_FORWARD(params)...);\
	else if constexpr (requires{ CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...); })\
		return CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...);\
	else if constexpr (requires{ CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...); })\
		return CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...);\
	else throw "failure!";\
	/*else static_assert(false, "Failed to find matching function `" CPPE_STRINGIFY(FUNCNAME) "` on `" CPPE_STRINGIFY(OBJECT) "`");*/\
}(OBJECT, __VA_ARGS__)



// #define CPPE_UFCS_TEMPLATE(...) CPPE_GET_UFCS_MACRO(__VA_ARGS__, CPPE_UFCS_TEMPLATE_FUNCTION, CPPE_UFCS_TEMPLATE_PROPERTY)(__VA_ARGS__)

#define CPPE_UFCS_TEMPLATE_PROPERTY(PROPNAME, OBJECT)\
[&] (auto&& obj) ALWAYS_INLINE_LAMBDA -> decltype(auto) {\
	if constexpr (requires{ CPPE_FORWARD(obj).template PROPNAME; }) {\
		if constexpr (std::is_const_v<std::remove_reference_t<decltype(obj)>>\
		  && std::is_volatile_v<std::remove_reference_t<decltype(obj)>>)\
		    return std::forward<std::add_lvalue_reference_t<std::add_cv_t<decltype(CPPE_FORWARD(obj).template PROPNAME)>>>(CPPE_FORWARD(obj).template PROPNAME);\
		else if constexpr (std::is_const_v<std::remove_reference_t<decltype(obj)>>)\
			return std::forward<std::add_lvalue_reference_t<std::add_const_t<decltype(CPPE_FORWARD(obj).template PROPNAME)>>>(CPPE_FORWARD(obj).template PROPNAME);\
		else if constexpr (std::is_volatile_v<std::remove_reference_t<decltype(obj)>>)\
			return std::forward<std::add_lvalue_reference_t<std::add_volatile_t<decltype(CPPE_FORWARD(obj).template PROPNAME)>>>(CPPE_FORWARD(obj).template PROPNAME);\
		else return std::forward<std::add_lvalue_reference_t<decltype(CPPE_FORWARD(obj).template PROPNAME)>>(CPPE_FORWARD(obj).template PROPNAME);\
	} else if constexpr (requires{ CPPE_FORWARD(obj).template PROPNAME(); })\
		return CPPE_FORWARD(obj).template PROPNAME();\
	else if constexpr (requires{ PROPNAME(CPPE_FORWARD(obj)); })\
		return PROPNAME(CPPE_FORWARD(obj));\
	else if constexpr (requires{ CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(PROPNAME)); })\
		return CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(PROPNAME));\
	else if constexpr (requires{ CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(PROPNAME)); })\
		return CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(PROPNAME));\
	else throw "failure!";\
	/*else static_assert(false, "Failed to find property or field `" CPPE_STRINGIFY(PROPNAME) "` on `" CPPE_STRINGIFY(OBJECT) "`");*/\
}(OBJECT)

#define CPPE_UFCS_TEMPLATE_FUNCTION(FUNCNAME, OBJECT, ...)\
[&] (auto&& obj, auto&& ...params) ALWAYS_INLINE_LAMBDA -> decltype(auto) {\
	if constexpr (requires{ CPPE_FORWARD(obj).template FUNCNAME(CPPE_FORWARD(params)...); })\
		return CPPE_FORWARD(obj).template FUNCNAME(CPPE_FORWARD(params)...);\
	else if constexpr (requires{ FUNCNAME(CPPE_FORWARD(obj), CPPE_FORWARD(params)...); })\
		return FUNCNAME(CPPE_FORWARD(obj), CPPE_FORWARD(params)...);\
	else if constexpr (requires{ CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...); })\
		return CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...);\
	else if constexpr (requires{ CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...); })\
		return CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...);\
	else throw "failure!";\
	/*else static_assert(false, "Failed to find matching function `" CPPE_STRINGIFY(FUNCNAME) "` on `" CPPE_STRINGIFY(OBJECT) "`");*/\
}(OBJECT, __VA_ARGS__)


// #define CPPE_UFCS_QUALIFIED(...) CPPE_GET_UFCS_MACRO(__VA_ARGS__, CPPE_UFCS_QUALIFIED_FUNCTION, CPPE_UFCS_QUALIFIED_PROPERTY)(__VA_ARGS__)

#define CPPE_UFCS_QUALIFIED_PROPERTY(PROPNAME, OBJECT)\
[&] (auto&& obj) ALWAYS_INLINE_LAMBDA -> decltype(auto) {\
	if constexpr (requires{ PROPNAME(CPPE_FORWARD(obj)); })\
		return PROPNAME(CPPE_FORWARD(obj));\
	else if constexpr (requires{ CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(PROPNAME)); })\
		return CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(PROPNAME));\
	else if constexpr (requires{ CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(PROPNAME)); })\
		return CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(PROPNAME));\
	else throw "failure!";\
	/*else static_assert(false, "Failed to find property or field `" CPPE_STRINGIFY(PROPNAME) "` on `" CPPE_STRINGIFY(OBJECT) "`");*/\
}(OBJECT)

#define CPPE_UFCS_QUALIFIED_FUNCTION(FUNCNAME, OBJECT, ...)\
[&] (auto&& obj, auto&& ...params) ALWAYS_INLINE_LAMBDA -> decltype(auto) {\
	if constexpr (requires{ FUNCNAME(CPPE_FORWARD(obj), CPPE_FORWARD(params)...); })\
		return FUNCNAME(CPPE_FORWARD(obj), CPPE_FORWARD(params)...);\
	else if constexpr (requires{ CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...); })\
		return CPPE_FORWARD(obj).CPPE_operator_forward(CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...);\
	else if constexpr (requires{ CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...); })\
		return CPPE_operator_forward(CPPE_FORWARD(obj), CPPE_STRINGIFY(FUNCNAME), CPPE_FORWARD(params)...);\
	else throw "failure!";\
	/* else static_assert(false, "Failed to find matching function `" CPPE_STRINGIFY(FUNCNAME) "` on `" CPPE_STRINGIFY(OBJECT) "`");*/\
}(OBJECT, __VA_ARGS__)


#include <string_view>

// template<typename... Args>
// auto CPPE_operator_forward(auto&& obj, std::string_view funcname, Args... args) {
// 	static_assert(false, "Failed to find a function!");
// 	return 0;
// }


// #include <map>
// #include <string>
// #include <string_view>

// template<typename Value>
// Value& CPPE_operator_forward(std::map<std::string, Value>& map, std::string_view key) {
// 	return map[std::string(key)];
// }

// template<typename Value>
// const Value& CPPE_operator_forward(const std::map<std::string, Value>& map, std::string_view key) {
// 	return map.at(std::string(key));
// }

// #include <iostream>
// struct S {
// 	int a;

// 	void print() {
// 		std::cout << a << std::endl;
// 	}

// 	void print(int o) {
// 		std::cout << a << (a == o ? " == " : " != ") << o << std::endl;
// 	}
// };

// #include <variant>

// template <typename T, typename... Ts>
// [[nodiscard]]
// static constexpr size_t index_of(const std::variant<Ts...>) noexcept {
// 	size_t r {0};
// 	const auto accumulator = [&r](const bool equ) noexcept {
// 		r += !equ;
// 		return equ;
// 	};
// 	(accumulator(std::is_same_v<T, Ts>) || ...);
// 	return r;
// }

// template <typename T, typename... Ts>
// [[nodiscard]]
// constexpr bool holds_type(const std::variant<Ts...>& var) noexcept {
// 	return var.index() == index_of<T>(var);
// }

// template <typename T, typename... Ts>
// [[nodiscard]]
// constexpr inline T value_or(const std::variant<Ts...>& var, const T&& instead) noexcept {
// 	return holds_type<T>(var) ? std::get<T>(var) : instead;
// } 

// void print2(S s) {
// 	std::cout << "Hello from print 2 s.a = " << s.a << std::endl;
// }

// #include <functional>

// int main() {
// 	std::map<std::string, S> map;
// 	map["bob"] = {1};
// 	map["sally"] = {2};
// 	map["larry"] = {3};


// 	// map.sally.a = 4
// 	// map->sally // CPPE_UFCS(*map, sally)
// 	CPPE_UFCS(a, CPPE_UFCS(sally, map)) = 4;
// 	// const auto& cmap = map;
// 	// auto& s2 = CPPE_UFCS(sally, cmap);
// 	// static_assert(std::is_same_v<decltype(CPPE_UFCS(a, s2)), const int&>, "not const int");
// 	// std::cout << CPPE_UFCS(a, s2) << std::endl;

// 	CPPE_UFCS(print, CPPE_UFCS(sally, map), 40);

// 	std::variant<int, std::string> var = 20; 
// 	std::cout << CPPE_UFCS_QUALIFIED(std::get<int>, var) << std::endl;
// }

#endif // __CPPE_UFCS_HPP__