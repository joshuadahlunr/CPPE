#ifndef __CPPE_CONTROL_FLOW__HPP__
#define __CPPE_CONTROL_FLOW__HPP__

#include "defer.hpp"

#define CPPE_STRINGIFY_IMPL(s) #s
#define CPPE_STRINGIFY(s) CPPE_STRINGIFY_IMPL(s)

namespace CPPE {
    template<size_t N>
    struct StringLiteral {
        constexpr StringLiteral(const char (&str)[N]) {         
          std::copy_n(str, N, value); }

        char value[N];
        auto operator<=>(const StringLiteral&) const = default;
        bool operator==(const StringLiteral&) const  = default;
    };


    template<typename T>
    struct return_ { T value; };
    template<> struct return_<void> {};

    template<typename T>
    struct yield_ { T value; };
    template<> struct yield_<void> {};

    template<StringLiteral Label>
    struct continue_ {
        constexpr bool operator==(continue_) { return true; }
        template<StringLiteral L> constexpr bool operator==(continue_<L>) { return false; }
    };

    template<StringLiteral Label>
    struct break_ {
        constexpr bool operator==(break_) { return true; }
        template<StringLiteral L> constexpr bool operator==(break_<L>) { return false; }
    };

    // template<typename Yield, typename Return = void, StringLiteral Label = "<invalid>">
    // struct propgiate : std::variant<Yield, return_<Return>, continue_<Label>, break_<Label>, std::exception_ptr> {
    //     using variant = std::variant<Yield, return_<Return>, continue_<Label>, break_<Label>, std::exception_ptr>;
    //     using value_type = Yield;
    //     using return_type = Return;
    //     static constexpr auto label = Label;

    //     using variant::variant;
    //     constexpr variant& v() { return *this; }

    //     template<size_t I>
    //     constexpr auto& get() { return std::get<I>(v()); }
    // };
}

// #define CPPE_PROPIGATE_EXPRESSION(out, LABEL, in) if(in.index() == 0)\
//         out = in.get<0>();\
//     else if(in.index() == 4) /*exception_ptr*/ std::rethrow_exception(in.get<4>())\
//     else if(in.index() == 2) { /*continue_*/ if constexpr(::CPPE::continue_<CPPE_STRINGIFY(LABEL)> == in.get<2>()) continue; }\
//     else if(in.index() == 3) { /*break_*/ if constexpr(::CPPE::break_<CPPE_STRINGIFY(LABEL)> == in.get<3>()) break; }\
//     else return in;
// #define CPPE_PROPIGATE_DEFINE_EXPRESSION_EXPLICIT(type, out, LABEL, in) type out; CPPE_PROPIGATE_EXPRESSION(out, LABEL, in)
// #define CPPE_PROPIGATE_DEFINE_EXPRESSION(out, LABEL, in) CPPE_PROPIGATE_DEFINE_EXPRESSION_EXPLICIT(decltype(in)::value_type, out, LABEL, in)

// #define CPPE_PROPIGATE(out, LABEL, in) if(in.index() == 0)\
//         out = std::get<0>(in.get<0>());\
//     else if(in.index() == 4) /*exception_ptr*/ std::rethrow_exception(in.get<4>())\
//     else if(in.index() == 1) /*return*/ return in.get<1>().value;\
//     else if(in.index() == 2) { /*continue_*/ if constexpr(::CPPE::continue_<CPPE_STRINGIFY(LABEL)> == in.get<2>()) continue; }\
//     else if(in.index() == 3) { /*break_*/ if constexpr(::CPPE::break_<CPPE_STRINGIFY(LABEL)> == in.get<3>()) break; }\
//     else return in;
// #define CPPE_PROPIGATE_DEFINE_EXPLICIT(type, out, LABEL, in) type out; CPPE_PROPIGATE(out, LABEL, in)
// #define CPPE_PROPIGATE_DEFINE(out, LABEL, in) CPPE_PROPIGATE_DEFINE_EXPLICIT(decltype(in)::value_type, out, LABEL, in)


// NOTE: Can't use goto since we need to jump between functions!
#define CPPE_DEFINE_CONTINUE_BREAK(LABEL) catch(::CPPE::continue_<CPPE_STRINGIFY(LABEL)>) { continue; } catch(::CPPE::break_<CPPE_STRINGIFY(LABEL)>) { break; }
#define CPPE_CONTINUE(LABEL) throw ::CPPE::continue_<CPPE_STRINGIFY(LABEL)>{};
#define CPPE_BREAK(LABEL) throw ::CPPE::break_<CPPE_STRINGIFY(LABEL)>{};
// #define CPPE_CONTINUE(LABEL) return ::CPPE::continue_<CPPE_STRINGIFY(LABEL)>{};
// #define CPPE_BREAK(LABEL) return ::CPPE::break_<CPPE_STRINGIFY(LABEL)>{};

#define CPPE_DEFINE_EXPRESSION_RETURN(type) catch(::CPPE::return_<type> r) { return r.value; } catch(::CPPE::yield_<type> r) { return r.value; }
#define CPPE_EXPRESSION_RETURN(value) throw ::CPPE::return_{value};
// #define CPPE_EXPRESSION_RETURN(value) return ::CPPE::return_{value};

#define CPPE_CONVERT_ARGC_ARGV(argc, argv) std::span(argv, argc) | std::views::transform([](char const* v){ return std::string_view(v); })
#define CPPE_CONVERT_ARGC_ARGV_TO(argc, argv, name, type) auto CPPE_##name = CPPE_CONVERT_ARGC_ARGV(argc, argv); type name(CPPE_##name.begin(), CPPE_##name.end());

#define CPPE_WILDCARD_IDENTIFIER DEFER_2(__LINE__)

#endif //__CPPE_CONTROL_FLOW__HPP__