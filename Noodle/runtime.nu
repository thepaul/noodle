# runtime
#
# Noodle runtime

(import NoodleMain)
(import error)

(define nu-compile .NoodleMain.noodle_compile)
(define nu-compile-str .NoodleMain.noodle_compile_str)
(define nu-error error)

(del NoodleMain)
(del error)

(defmacro (mreduce seq op)
  """Macro-reduce"""
  (let ((elem (gensym))
        (first (gensym))
        (sequence (gensym)))
    `(let ((,sequence ,seq))
       (if (== 0 (len ,sequence))
           0
           (let ((,first (subscript ,sequence 0)))
             (for ,elem in (subscript ,sequence (slice 1 None))
               (= ,first (,op ,first ,elem)))
             ,first)))))

(defmacro (simple-math-op symbol)
  `(define (,symbol @terms)
     (mreduce terms ,symbol)))

(defmacro (simple-math-ops @symbols)
  `(begin ,@(for-tuple sym in symbols
              `(simple-math-op ,sym))))

(defmacro (math-op-special-cased symbol)
  `(define (,symbol @terms)
     (if (== (len terms) 1)
         (,symbol [terms 0])
         (mreduce terms ,symbol))))

(defmacro (math-ops-special-cased @symbols)
  `(begin ,@(for-tuple sym in symbols
              `(math-op-special-cased ,sym))))

(defmacro (func-to-match-macro sym)
  `(define (,sym arg)
     (,sym arg)))

(defmacro (funcs-to-match-macros @symbols)
  `(begin ,@(for-tuple sym in symbols
              `(func-to-match-macro ,sym))))

(simple-math-ops * % ** & ^ |)
(math-ops-special-cased + - / >> <<)
(funcs-to-match-macros ~ not)

(defmacro (make-comparer-func op)
  `(define (,op @args)
     (let ((argiter (get-iter args))
           (earlier (.argiter.next)))
       (iterate-over arg argiter
         (if (,op earlier arg)
             (= earlier arg)
             (return False))))
     True))

(defmacro (make-comparer-funcs @ops)
  `(begin ,@(for-tuple sym in ops
              `(make-comparer-func ,sym))))

(make-comparer-funcs == != > < >= <= in is not-in is-not)

# This allows users to put " ;" at the end of an interactive command
# to suppress printing the result (since the result will become None).
(define ; None)

(= _items {})
((lambda (i)  # avoid adding to globals while iterating over globals
   (for (k v) in (.(globals).iteritems)
     (if (not (.k.startswith '_')) (= [i k] v))))
 _items)

(define __all__ (._items.keys))
