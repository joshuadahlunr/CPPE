#ifndef __CPPE_PRODUCT_SUM_HPP__
#define __CPPE_PRODUCT_SUM_HPP__

#include <variant>
#include <span>

namespace CPPE {
	template<typename... Ts>
	struct typelist {};

	template<typename... Ts>
	struct make_list {
		using type = typelist<Ts...>;
	};

	template<typename... Ts>
	struct make_list<typelist<Ts...>> {
		using type = typelist<Ts...>;
	};

	template<typename... Ts>
	struct make_list<std::variant<Ts...>> {
		using type = typelist<Ts...>;
	};

	// template<typename... Ts>
	// struct make_list<std::tuple<Ts...>> {
	// 	using type = typelist<Ts...>;
	// };

	template<typename... Ts>
	using make_list_t = typename make_list<Ts...>::type;


	template<typename... Ts>
	struct make_variant {
		using type = std::variant<Ts...>;
	};

	template<typename... Ts>
	struct make_variant<typelist<Ts...>> {
		using type = std::variant<Ts...>;
	};

	template<typename... Ts>
	using make_variant_t = typename make_variant<Ts...>::type;


	// template<typename... Ts>
	// struct make_tuple {
	// 	using type = std::tuple<Ts...>;
	// };

	// template<typename... Ts>
	// struct make_tuple<std::tuple<Ts...>> {
	// 	using type = std::tuple<Ts...>;
	// };

	// template<typename... Ts>
	// struct make_tuple<typelist<Ts...>> {
	// 	using type = std::tuple<Ts...>;
	// };

	// template<typename... Ts>
	// using make_tuple_t = typename make_tuple<Ts...>::type;



	template<typename T1, typename T2>
	struct concat {
		using type = typelist<T1, T2>;
	};

	template<typename... TL1, typename... TL2>
	struct concat<typelist<TL1...>, typelist<TL2...>> {
		using type = typelist<TL1..., TL2...>;
	};

	template<typename T1, typename T2>
	using concat_t = typename concat<T1, T2>::type;


	// Flatten a single type into the type
	template<typename T>
	struct flatten {
		using type = typelist<T>;
	};

	// Flatten a list of a single type into the type
	template<typename T>
	struct flatten<typelist<T>> {
		using type = typename flatten<T>::type;
	};

	// Recursively flatten 
	template<typename THead, typename Ttwo, typename... Ttail>
	struct flatten<typelist<THead, Ttwo, Ttail...>> {
		// using type = decltype(std::tuple_cat(make_tuple_t<typename flatten<make_list_t<Ts>>::type>{}...));
		using type = concat_t<typename flatten<make_list_t<THead>>::type, typename flatten<typelist<make_list_t<Ttwo>, Ttail...>>::type>;
	};

	template<typename Tlist>
	// using flatten_t = make_list_t<typename flatten<Tlist>::type>;
	using flatten_t = typename flatten<Tlist>::type;



	// Helper metafunction to check if a type exists in the typelist
	template <typename T, typename... Ts>
	struct is_in : std::disjunction<std::is_same<T, Ts>...> {};

	template <typename T, typename... Ts>
	struct is_in<T, typelist<Ts...>> : std::disjunction<std::is_same<T, Ts>...> {};

	template <typename T, typename... Ts>
	inline constexpr bool is_in_v = is_in<T, Ts...>::value;


	// Helper metafunction to check if all types in one typelist are present in another typelist
	template <typename TL1, typename TL2>
	struct all_in;

	// Error case: T2 not a list!
	template <typename TL2>
	struct all_in<typelist<>, TL2> : std::false_type {};

	// Base case: Empty typelist
	template <typename... TL2>
	struct all_in<typelist<>, typelist<TL2...>> : std::true_type {};

	// Recursive case: Check if the first type is in TL2 and continue with the rest of the typelist
	template <typename T, typename... Ts, typename TL2>
	struct all_in<typelist<T, Ts...>, TL2> {
		static constexpr bool value = is_in_v<T, TL2> && all_in<typelist<Ts...>, TL2>::value;
	};

	// Helper function to check if all types in one typelist are in another typelist
	template <typename TL1, typename TL2>
	inline constexpr bool all_in_v = all_in<TL1, TL2>::value;



	// Helper metafunction to remove duplicates from the typelist
	template <typename TL, typename... Ts>
	struct unique_list_impl;

	template <typename... Ts, typename T>
	struct unique_list_impl<typelist<Ts...>, T> {
		using type = std::conditional_t<is_in<T, Ts...>::value, typelist<Ts...>, typelist<Ts..., T>>;
	};

	template <typename... Ts, typename T, typename... Rest>
	struct unique_list_impl<typelist<Ts...>, T, Rest...> {
		using type = std::conditional_t<is_in<T, Ts...>::value, typename unique_list_impl<typelist<Ts...>, Rest...>::type, typename unique_list_impl<typelist<Ts..., T>, Rest...>::type>;
	};

	// Metafunction to remove duplicates from the typelist
	template <typename TL>
	struct unique_list;

	template <typename... Ts>
	struct unique_list<typelist<Ts...>> {
		using type = typename unique_list_impl<typelist<>, Ts...>::type;
	};

	template<typename... Ts>
	using unique_list_t = typename unique_list<Ts...>::type;



	template<typename Tto, typename Tfrom>
	struct is_super_set : std::false_type {};

	template<typename... Ttos, typename... Tfroms>
	struct is_super_set<typelist<Ttos...>, typelist<Tfroms...>> {
		using fromList = unique_list_t<flatten_t<typelist<Tfroms...>>>;
		using toList = unique_list_t<flatten_t<typelist<Ttos...>>>;
		static constexpr bool value = std::conditional_t<all_in_v<fromList, toList>, std::true_type, std::false_type>::value;
	};

	template<typename... Ttos, typename... Tfroms>
	struct is_super_set<std::variant<Ttos...>, std::variant<Tfroms...>> : is_super_set<typelist<Ttos...>, typelist<Tfroms...>> {};

	template<typename Tto, typename Tfrom>
	inline constexpr bool is_super_set_v = is_super_set<Tto, Tfrom>::value;


	template<typename T>
	struct void_to_mono {
		using type = T;
	};

	template<>
	struct void_to_mono<void> {
		using type = std::monostate;
	};

	template<typename T>
	using void_to_mono_t = typename void_to_mono<T>::type;




	template<typename T>
	struct c_array_impl {
		using type = T[];
	};

	template<typename T>
	struct c_array_impl<std::vector<T>> {
		using type = T[];
	};

	template<typename T, size_t Size>
	struct c_array_impl<std::array<T, Size>> {
		using type = T[Size];
	};

	template<typename T, size_t Size>
	struct c_array_impl<std::span<T, Size>> {
		using type = std::conditional_t<Size == std::dynamic_extent, T[], T[Size]>;
	};

	template<typename T, size_t Size>
	struct c_array_impl<T[Size]> {
		using type = T[Size];
	};

	template<typename T>
	using c_array = typename c_array_impl<T>::type;

	template<typename T>
	using alien_memory = volatile T;




	template<typename... Ts>
	struct sum {
		using type = typename sum<unique_list_t<flatten_t<typelist<Ts...>>>>::type;
	};

	template<typename T>
	struct sum<T> {
		using type = T;
	};

	template<typename T>
	struct sum<typelist<T>> {
		using type = T;
	};

	template<typename... Ts>
	struct sum<typelist<Ts...>> {
		using type = make_variant_t<typelist<void_to_mono_t<Ts>...>>;
	};

	template<typename... Ts>
	using sum_t = typename sum<Ts...>::type;


	template<typename... Ts>
	struct product {
		using type = std::tuple<Ts...>;
	};

	template<typename T>
	struct product<T> {
		using type = T;
	};

	template<typename T>
	struct product<std::tuple<T>> {
		using type = T;
	};

	template<typename... Ts>
	struct product<std::tuple<Ts...>> {
		using type = std::tuple<Ts...>;
	};

	template<typename... Ts>
	using product_t = typename product<Ts...>::type;


	template<typename To, typename... Froms>
	To promote(std::variant<Froms...>&& from) {
		static_assert(is_super_set_v<make_list_t<To>, typelist<Froms...>>, "The type you are converting to must be a super set of the type you are converting from!");
		return std::visit<To>([](auto&& value) { return std::move(value); }, std::move(from));
	}

	template<typename To, typename From>
	To promote(From&& from) {
		static_assert(is_super_set_v<make_list_t<To>, typelist<From>>, "The type you are converting to must be a super set of the type you are converting from!");
		return std::move(from);
	}

	#define CPPE_PROMOTE(type, expression) [&] () -> type {\
		if constexpr(std::is_same_v<decltype(expression), void>) {\
			expression;\
			return {};\
		} else return ::CPPE::promote<type>(expression);\
	}()



	// Unit Tests
	static_assert(is_super_set_v<std::variant<int, short, long>, std::variant<int>>);
	static_assert(!is_super_set_v<std::variant<short, long>, std::variant<std::string>>); 
	static_assert(is_super_set_v<std::variant<int, short, long>, std::variant<int, short, long>>);

	static_assert(std::is_same_v< sum_t<int>, int >);
	static_assert(std::is_same_v< sum_t<int, int>, int >);
	static_assert(std::is_same_v< sum_t<int, short, long>, std::variant<int, short, long>  >);
	static_assert(std::is_same_v< sum_t<int, short, long, short>, std::variant<int, short, long>  >);
	static_assert(std::is_same_v< sum_t<int, std::variant<short, long>>, std::variant<int, short, long> >);
	static_assert(std::is_same_v< sum_t<int, std::variant<short, long, short>>, std::variant<int, short, long> >);
	static_assert(std::is_same_v< sum_t<int, std::tuple<short, long>>, std::variant<int, std::tuple<short, long>> >);

	static_assert(std::is_same_v< product_t<int>, int >);
	static_assert(std::is_same_v< product_t<sum_t<int, std::string>>, std::variant<int, std::string> >);
	static_assert(std::is_same_v< product_t<int, int>, std::tuple<int, int> >);
	static_assert(std::is_same_v< product_t<int, product_t<int, std::string>>, std::tuple<int, std::tuple<int, std::string>> >);
	static_assert(std::is_same_v< product_t<int, sum_t<int, std::string>>, std::tuple<int, std::variant<int, std::string>> >);
}

// Overloads of std::get so that std::get<0>(anything) will now work... so code can consitently be written for all sum_t
namespace std {
	template<size_t I, typename T>
	const T& get(const T& v) { 
		static_assert(I == 0, "Non variant/collection values can only have their first value gotten!");
		return v;
	}

	template<size_t I, typename T>
	T& get(T& v) { 
		static_assert(I == 0, "Non variant/collection values can only have their first value gotten!");
		return v;
	}

	template<size_t I, typename T>
	T get(T&& v) { 
		static_assert(I == 0, "Non variant/collection values can only have their first value gotten!");
		return v;
	} 
}

using CPPE::c_array;
using CPPE::alien_memory;




// int | string == CPPE::sum_t<int, string>
// (int, string) == CPPE::product_t<int, string>
// (int | string) == CPPE::product_t<CPPE::sum_t<int, string>> == CPPE::sum_t<int, string>
// c_array<int[5]> == c_array<std::array<int 5>> == int[5]

#endif // __CPPE_PRODUCT_SUM_HPP__