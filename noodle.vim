" Vim syntax file
" Language:	Noodle
" Maintainer:	paul cannon <paul@nafpik.com>
" Updated:	2005-04-09

" For version 5.x: Clear all syntax items
" For version 6.x: Quit when a syntax file was already loaded
if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif


if version < 600
  set      iskeyword=33,36-38,42-43,45,47-57,60-90,94,95,97-122,124,126
  set      cpoptions+=M
else
  setlocal iskeyword=33,36-38,42-43,45,47-57,60-90,94,95,97-122,124,126
  setlocal cpoptions+=M
endif

syn keyword noodleBuiltin	break continue macroexpand-1
syn keyword noodleBuiltin	except exec finally let gensym
syn keyword noodleBuiltin	print print-item print-newline
syn keyword noodleBuiltin	print-to print-item-to print-newline-to
syn keyword noodleBuiltin	raise getattribute setattribute
syn keyword noodleBuiltin	del delsubscript del-value
syn keyword noodleBuiltin	return try begin apply get-iter
syn keyword noodleBuiltin	global assert else setsubscript
syn keyword noodleBuiltin	lambda yield class anon-class
syn keyword noodleBuiltin	define defmacro = defmethod undefmacro
syn keyword noodleBuiltin	and or == > >= <= < ! != not ~
syn keyword noodleBuiltin	for while if cond for-iter for-list when
syn keyword noodleBuiltin	mktuple mklist mkdict subscript mkslice
syn keyword noodleBuiltin	comment is in is-not not-in unless
syn keyword noodleBuiltin       import import-from import-all-from
syn keyword noodleBuiltin	+ - / // % << >> & ^
syn keyword noodleBuiltin	+= -= *= /= //= **= %= <<= >>= &= ^=
syn keyword noodleBuiltin       nu-eval nu-eval-str set-attr set-attrs
syn keyword noodleBuiltin       quote quasiquote unquote for-tuple
syn keyword noodleBuiltin       toggle iterate-over printf printf-to
syn keyword noodleBuiltin       printnonl printnonl-to
syn keyword noodleBuiltin       all-true all-false double triple half
syn keyword noodleBuiltin       get-module get-from-module
syn match   noodleBuiltin       "\<\*\_[])}:[:space:]]"me=e-1
syn match   noodleBuiltin       "\<\*\*\_[])}:[:space:]]"me=e-1
syn match   noodleBuiltin       "\<|\>"
syn match   noodleBuiltin       "\<|=\>"

syn match   noodleComment	"#.*$" contains=noodleTodo
syn keyword noodleTodo		TODO FIXME XXX contained

" strings
syn region noodleString		matchgroup=Normal start=+[uU]\='+ end=+'+ skip=+\\\\\|\\'+ contains=noodleEscape
syn region noodleString		matchgroup=Normal start=+[uU]\="+ end=+"+ skip=+\\\\\|\\"+ contains=noodleEscape
syn region noodleString		matchgroup=Normal start=+[uU]\="""+ end=+"""+ skip=+\\\\\|\\"+ contains=noodleEscape
syn region noodleString		matchgroup=Normal start=+[uU]\='''+ end=+'''+ skip=+\\\\\|\\'+ contains=noodleEscape
syn region noodleRawString	matchgroup=Normal start=+[uU]\=[rR]'+ end=+'+ skip=+\\\\\|\\'+
syn region noodleRawString	matchgroup=Normal start=+[uU]\=[rR]"+ end=+"+ skip=+\\\\\|\\"+
syn region noodleRawString	matchgroup=Normal start=+[uU]\=[rR]"""+ end=+"""+ skip=+\\\\\|\\"+
syn region noodleRawString	matchgroup=Normal start=+[uU]\=[rR]'''+ end=+'''+ skip=+\\\\\|\\'+
syn match  noodleEscape		+\\[abfnrtv'"\\]+ contained
syn match  noodleEscape		"\\\o\{1,3}" contained
syn match  noodleEscape		"\\x\x\{2}" contained
syn match  noodleEscape		"\(\\u\x\{4}\|\\U\x\{8}\)" contained

syn match   noodleNumber	"\<[-+]\=0x\x\+[Ll]\=\>"
syn match   noodleNumber	"\<[-+]\=\d\+\([eE][+-]\=\d\+\)\=[LljJ]\=\>"
syn match   noodleNumber	"\<[-+]\=\.\d\+\([eE][+-]\=\d\+\)\=[jJ]\=\>"
syn match   noodleNumber	"\<[-+]\=\d\+\.\([eE][+-]\=\d\+\)\=[jJ]\=\>"
syn match   noodleNumber	"\<[-+]\=\d\+\.\d\+\([eE][+-]\=\d\+\)\=[jJ]\=\>"

syn keyword noodleConstant	True False None

if exists("python_highlight_builtins")
  " builtin functions, types and objects, not really part of the syntax
  syn keyword pythonBuiltin	Ellipsis None NotImplemented __import__ abs
  syn keyword pythonBuiltin	apply buffer callable chr classmethod cmp
  syn keyword pythonBuiltin	coerce compile complex delattr dict dir divmod
  syn keyword pythonBuiltin	eval execfile file filter float getattr globals
  syn keyword pythonBuiltin	hasattr hash hex id input int intern isinstance
  syn keyword pythonBuiltin	issubclass iter len list locals long map max
  syn keyword pythonBuiltin	min object oct open ord pow property range
  syn keyword pythonBuiltin	raw_input reduce reload repr round setattr
  syn keyword pythonBuiltin	slice staticmethod str super tuple type unichr
  syn keyword pythonBuiltin	unicode vars xrange zip
endif

if exists("python_highlight_exceptions")
  " builtin exceptions and warnings
  syn keyword pythonException	ArithmeticError AssertionError AttributeError
  syn keyword pythonException	DeprecationWarning EOFError EnvironmentError
  syn keyword pythonException	Exception FloatingPointError IOError
  syn keyword pythonException	ImportError IndentationError IndexError
  syn keyword pythonException	KeyError KeyboardInterrupt LookupError
  syn keyword pythonException	MemoryError NameError NotImplementedError
  syn keyword pythonException	OSError OverflowError OverflowWarning
  syn keyword pythonException	ReferenceError RuntimeError RuntimeWarning
  syn keyword pythonException	StandardError StopIteration SyntaxError
  syn keyword pythonException	SyntaxWarning SystemError SystemExit TabError
  syn keyword pythonException	TypeError UnboundLocalError UnicodeError
  syn keyword pythonException	UserWarning ValueError Warning WindowsError
  syn keyword pythonException	ZeroDivisionError
endif

if version >= 508 || !exists("did_noodle_syn_inits")
  if version <= 508
    let did_noodle_syn_inits = 1
    command -nargs=+ HiLink hi link <args>
  else
    command -nargs=+ HiLink hi def link <args>
  endif

  " The default methods for highlighting.  Can be overridden later
  HiLink noodleBuiltin		Statement
  HiLink noodleString		String
  HiLink noodleRawString	String
  HiLink noodleConstant         Type
  HiLink noodleEscape		Special
  HiLink noodleComment		Comment
  HiLink noodleTodo		Todo
  HiLink noodleNumber		Number
  if exists("python_highlight_builtins")
    HiLink pythonBuiltin	Function
  endif
  if exists("python_highlight_exceptions")
    HiLink pythonException	Exception
  endif

  delcommand HiLink
endif

let b:current_syntax = "noodle"

" vim: ts=8 noet
