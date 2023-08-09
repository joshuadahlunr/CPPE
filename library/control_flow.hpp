#ifndef __CPPE_CONTROL_FLOW__HPP__
#define __CPPE_CONTROL_FLOW__HPP__

#include "defer.hpp"

#define CPPE_STRINGIFY_IMPL(s) #s
#define CPPE_STRINGIFY(s) CPPE_STRINGIFY_IMPL(s)

#if __cpp_exceptions
    #define CPPE_THROW(x) throw x
#else
    #define CPPE_THROW(x) (void)x; std::terminate()
#endif

namespace CPPE {
    template<size_t N>
    struct StringLiteral {
        constexpr StringLiteral(const char (&str)[N]) {         
          std::copy_n(str, N, value); }

        char value[N];
        auto operator<=>(const StringLiteral&) const = default;
        bool operator==(const StringLiteral&) const = default;
    };

    struct FlowPropigationException: std::runtime_error {
        using std::runtime_error::runtime_error;
    };


    // template<typename T>
    // struct return_ { T value; };
    // template<> struct return_<void> {};

    // template<typename T>
    // struct yield_ { T value; };
    // template<> struct yield_<void> {};

    // template<StringLiteral Label>
    // struct continue_ {
    //     constexpr bool operator==(continue_) { return true; }
    //     template<StringLiteral L> constexpr bool operator==(continue_<L>) { return false; }
    // };

    // template<StringLiteral Label>
    // struct break_ {
    //     constexpr bool operator==(break_) { return true; }
    //     template<StringLiteral L> constexpr bool operator==(break_<L>) { return false; }
    // };

    struct Propigate {
        virtual ~Propigate() {}
        virtual void deleter() = 0;

        enum class Type {
            NONE,
            RETURN,
            CONTINUE,
            BREAK,
            EXCEPTION
        } type;
    };

    template<typename R>
    struct Return : Propigate {
        R value;
        Return(R&& value) : value(std::move(value)) {}
        void deleter() override { delete this; }
    };
    template<>
    struct Return<void> : Propigate {
        void deleter() override { delete this; }
    };
    template<typename R>
    struct Yield : Return<R> {};

    struct Exception : Propigate {
        std::exception_ptr ptr;
        Exception(std::exception_ptr ptr) : ptr(ptr) {}
        void deleter() override { delete this; }
    };

    struct BaseCB : Propigate {
        const char* label;
        void deleter() override { delete this; }
    };

    template<StringLiteral Label>
    struct Continue : BaseCB { 
        Continue() { label = Label.value; } 
        constexpr bool operator==(Continue) { return true; }
        template<StringLiteral L> constexpr bool operator==(Continue<L>) { return false; }
    };
    template<StringLiteral Label>
    struct Break : BaseCB { 
        Break() { label = Label.value; } 
        constexpr bool operator==(Break) { return true; }
        template<StringLiteral L> constexpr bool operator==(Break<L>) { return false; }
    };

  

    struct JumpState {
        std::jmp_buf state;
        Propigate* propigate_ = nullptr;
        Propigate::Type type;
        JumpState* parent = nullptr;
        

        template<typename T>
        T& propigate() { return *static_cast<T*>(propigate_); }

        void jump() { std::longjmp(state, true); }

        template<typename T>
        void return_(T&& value) {
            propigate_ = new Return<int>(std::move(value));
            type = Propigate::Type::RETURN;
            jump();
        }

        void throw_(std::exception_ptr ptr) {
            propigate_ = new Exception(ptr);
            type = Propigate::Type::EXCEPTION;
            jump();
        }

        template<StringLiteral L>
        void continue_() {
            propigate_ = new Continue<L>();
            type = Propigate::Type::CONTINUE;
            jump();
        }

        template<StringLiteral L>
        void break_() {
            propigate_ = new Break<L>();
            type = Propigate::Type::BREAK;
            jump();
        }
    };
}


#define CPPE_CONVERT_ARGC_ARGV(argc, argv) std::span(argv, argc) | std::views::transform([](char const* v){ return std::string_view(v); })
#define CPPE_CONVERT_ARGC_ARGV_TO(argc, argv, type, name) auto CPPE__##name = CPPE_CONVERT_ARGC_ARGV(argc, argv); type name(CPPE__##name.begin(), CPPE__##name.end());



#if __cpp_exceptions

    #define CPPE_DEFINE_PROPIGATOR_START(LABEL, TYPE, PARENT, DEPTH) try {
    #define CPPE_DEFINE_PROPIGATOR_END(LABEL, TYPE) } catch(::CPPE::Return<TYPE>& r) { return r.value; } catch(::CPPE::BaseCB& cb) { throw ::CPPE::FlowPropigationException("Uncaught Continue/Break with label: " + std::string(cb.label)); }
    #define CPPE_DEFINE_LOOP_PROPIGATOR_START(LABEL, TYPE, PARENT, DEPTH) try {
    #define CPPE_DEFINE_LOOP_PROPIGATOR_END(LABEL, TYPE) } catch(::CPPE::Continue<CPPE_STRINGIFY(LABEL)>&) { continue; } catch(::CPPE::Break<CPPE_STRINGIFY(LABEL)>&) { break; }

    #define CPPE_DEFINE_LOOP_HELPER_PROPIGATOR(DEPTH)

    #define CPPE_YIELD(VALUE, DEPTH) return VALUE
    #define CPPE_RETURN(VALUE, DEPTH) throw ::CPPE::Return{VALUE};
    #define CPPE_CONTINUE(LABEL, DEPTH) throw ::CPPE::Continue<CPPE_STRINGIFY(LABEL)>{};
    #define CPPE_BREAK(LABEL, DEPTH) throw ::CPPE::Break<CPPE_STRINGIFY(LABEL)>{};

#else // no __cpp_exceptions

     // NOTE: Can't use goto since we need to jump between functions!
    #define CPPE_DEFINE_PROPIGATOR_START(LABEL, TYPE, PARENT, DEPTH) ::CPPE::JumpState CPPE_propigate_##DEPTH;\
        CPPE_propigate_##DEPTH.parent = PARENT;\
        [[unlikely]] if(setjmp(CPPE_propigate_##DEPTH.state)) {\
            [[likely]] if(CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::CONTINUE or CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::BREAK) {\
                auto& cb = CPPE_propigate_##DEPTH.propigate<::CPPE::BaseCB>();\
                /*if (cb.label == CPPE_STRINGIFY(LABEL)) {\
                    cb.deleter();\
                    if(CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::CONTINUE)\
                        continue;\
                    else if (CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::BREAK)\
                        break;\
                } else*/ if(CPPE_propigate_##DEPTH.parent){\
                    /* Rethrow to parent */\
                    CPPE_propigate_##DEPTH.parent->propigate_ = CPPE_propigate_##DEPTH.propigate_;\
                    CPPE_propigate_##DEPTH.parent->type = CPPE_propigate_##DEPTH.type;\
                    CPPE_propigate_##DEPTH.parent->jump();\
                } else {\
                    std::string label = cb.label;\
                    cb.deleter();\
                    CPPE_THROW(::CPPE::FlowPropigationException("Uncaught Continue/Break with label: " + label));\
                }\
            } else if(CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::RETURN) {\
                auto& r = CPPE_propigate_##DEPTH.propigate<::CPPE::Return<TYPE>>();\
                decltype(auto) ret = std::move(r.value);\
                r.deleter();\
                return ret;\
            } else if(CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::EXCEPTION) {\
                auto& e = CPPE_propigate_##DEPTH.propigate<::CPPE::Exception>();\
                std::exception_ptr ptr = e.ptr;\
                e.deleter();\
                std::rethrow_exception(ptr);\
            } else CPPE_THROW(::CPPE::FlowPropigationException("Propigate Set but its type is None!"));\
        }

    #define CPPE_DEFINE_LOOP_PROPIGATOR_START(LABEL, TYPE, PARENT, DEPTH) ::CPPE::JumpState CPPE_propigate_##DEPTH;\
        CPPE_propigate_##DEPTH.parent = PARENT;\
        CPPE_propigate_helper_##DEPTH.parent = &CPPE_propigate_##DEPTH;\
        [[unlikely]] if(setjmp(CPPE_propigate_##DEPTH.state)) {\
            [[likely]] if(CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::CONTINUE or CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::BREAK) {\
                auto& cb = CPPE_propigate_##DEPTH.propigate<::CPPE::BaseCB>();\
                if (cb.label == std::string(CPPE_STRINGIFY(LABEL))) {\
                    cb.deleter();\
                    if(CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::CONTINUE)\
                        continue;\
                    else if (CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::BREAK)\
                        break;\
                } else if(CPPE_propigate_##DEPTH.parent){\
                    /* Rethrow to parent */\
                    CPPE_propigate_##DEPTH.parent->propigate_ = CPPE_propigate_##DEPTH.propigate_;\
                    CPPE_propigate_##DEPTH.parent->type = CPPE_propigate_##DEPTH.type;\
                    CPPE_propigate_##DEPTH.parent->jump();\
                } else {\
                    std::string label = cb.label;\
                    cb.deleter();\
                    CPPE_THROW(::CPPE::FlowPropigationException("Uncaught Continue/Break with label: " + label));\
                }\
            } else if(CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::RETURN) {\
                /* Rethrow to parent */\
                CPPE_propigate_##DEPTH.parent->propigate_ = CPPE_propigate_##DEPTH.propigate_;\
                CPPE_propigate_##DEPTH.parent->type = CPPE_propigate_##DEPTH.type;\
                CPPE_propigate_##DEPTH.parent->jump();\
            } else if(CPPE_propigate_##DEPTH.type == ::CPPE::Propigate::Type::EXCEPTION) {\
                auto& e = CPPE_propigate_##DEPTH.propigate<::CPPE::Exception>();\
                std::exception_ptr ptr = e.ptr;\
                e.deleter();\
                std::rethrow_exception(ptr);\
            } else CPPE_THROW(::CPPE::FlowPropigationException("Propigate Set but its type is None!"));\
        } 

    #define CPPE_DEFINE_LOOP_HELPER_PROPIGATOR(DEPTH) ::CPPE::JumpState CPPE_propigate_helper_##DEPTH;\
        [[unlikely]] if(setjmp(CPPE_propigate_helper_##DEPTH.state)) {\
            /* Rethrow to parent */\
            CPPE_propigate_helper_##DEPTH.parent->propigate_ = CPPE_propigate_helper_##DEPTH.propigate_;\
            CPPE_propigate_helper_##DEPTH.parent->type = CPPE_propigate_helper_##DEPTH.type;\
            CPPE_propigate_helper_##DEPTH.parent->jump();\
        }

    #define CPPE_DEFINE_PROPIGATOR_END(LABEL, TYPE)
    #define CPPE_DEFINE_LOOP_PROPIGATOR_END(LABEL, TYPE)

    #define CPPE_YIELD(VALUE, DEPTH) return VALUE
    #define CPPE_RETURN(VALUE, DEPTH) CPPE_propigate_##DEPTH.return_(VALUE)
    #define CPPE_CONTINUE(LABEL, DEPTH) CPPE_propigate_helper_##DEPTH.continue_<CPPE_STRINGIFY(LABEL)>()
    #define CPPE_BREAK(LABEL, DEPTH) CPPE_propigate_helper_##DEPTH.break_<CPPE_STRINGIFY(LABEL)>()

#endif // __cpp_exceptions

#define CPPE_DEFINE_LOOP_PROPIGATOR_AND_HELPER_START(LABEL, TYPE, PARENT, DEPTH)\
    CPPE_DEFINE_LOOP_HELPER_PROPIGATOR(DEPTH)\
    CPPE_DEFINE_LOOP_PROPIGATOR_START(LABEL, TYPE, PARENT, DEPTH)

#endif //__CPPE_CONTROL_FLOW__HPP__