# macros.nu
#
# The macros here must depend only on special operators and Python builtin
# functions. Macros needing to depend on functions from the Noodle runtime
# should be defined elsewhere (nowhere is set up yet).

(import-from error NoodleSyntaxError)

(defmacro (set-attrs obj attrdict)
  (let ((o (gensym)))
    `(let ((,o ,obj))
       (for (k v) in ((getattribute ,attrdict 'iteritems')) (setattr ,o k v))
       ,o)))

(defmacro (-nu-abstract-errors @code)
    `(try
         (begin ,@code)
       (except (.nu-error.NoodleError ne)
         (raise ne))))

(defmacro (nu-eval codetree globs:None locs:None filename:'-' linenums:None)
    `(-nu-abstract-errors
       (eval (nu-compile ,codetree ,filename ,linenums) ,globs ,locs)))

(defmacro (nu-eval-str codestring globs:None locs:None filename:'-')
    `(-nu-abstract-errors
       (eval (nu-compile-str ,codestring ,filename) ,globs ,locs)))

(defmacro (toggle var)
    # TODO: allow for possibility of several variables
    `(= ,var (not ,var)))

(defmacro (comment @args) None)

(defmacro (for varname in_w iter @body)
    (if (!= in_w (mksymbol 'in'))
        (raise (NoodleSyntaxError
                "Bad for call: should be 'for varname in iter'")))
    `(iterate-over ,varname (get-iter ,iter) ,@body))

(defmacro (for-list varname in_w iter @body)
    (if (!= in_w (mksymbol 'in'))
        (raise (NoodleSyntaxError
                "Bad for-list call: should be 'for-list varname in iter'")))
    (= buildlist (gensym))
    `(let ((,buildlist []))
         (iterate-over ,varname (get-iter ,iter)
             (-list-append- ,buildlist (begin ,@body)))
         (del-value ,buildlist)))

(defmacro (for-iter varname in_w iter @body)
    (if (!= in_w (mksymbol 'in'))
        (raise (NoodleSyntaxError
                "Bad for-iter call: should be 'for-iter varname in iter'")))
    (= iterable (gensym))
    `((lambda (,iterable)
          (iterate-over ,varname ,iterable (yield (begin ,@body))))
      (get-iter ,iter)))

(defmacro (for-tuple varname in_w iter @body)
  `(tuple (for-list ,varname ,in_w ,iter ,@body)))

(defmacro (print @args)
  `(prog1 ,@(for-tuple arg in args `(print-item ,arg))
          (print-newline)))

(defmacro (printnonl @args)
  `(begin
     ,@(for-tuple arg in args `(print-item ,arg))))

(defmacro (printf template @args)
  `(print-item (% ,template \(,@args))))

(defmacro (print-to f @args)
  (= outfile (gensym))
  `(let ((,outfile ,f))
     (prog1 ,@(for-tuple arg in args `(print-item-to ,outfile ,arg))
            (print-newline-to ,outfile))))

(defmacro (printnonl-to f @args)
  `(begin
     ,@(for-tuple arg in args `(print-item-to ,f ,arg))))

(defmacro (printf-to f template @args)
  `(print-item-to ,f (% ,template \(,@args))))

(defmacro (when condition @body)
  `(if ,condition (begin ,@body)))

(defmacro (unless condition @body)
  `(if ,condition None (begin ,@body)))

(defmacro (all-true sequence)
  (= piece (gensym))
  `(begin
     (for ,piece in ,sequence
       (unless ,piece (return False)))
     True))

(defmacro (all-false sequence)
  (= piece (gensym))
  `(begin
     (for ,piece in ,sequence
       (if ,piece (return False)))
     True))

# compile-time calculations

(defmacro (double num)
  (* num 2))

(defmacro (triple num)
  (* num 3))

(defmacro (half num)
  (/ num 2))
