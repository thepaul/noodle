# interactive
#
# noodle interpreter

(import sys)
(import NoodleMain)
(import .Noodle.error)
(import-all-from .Noodle.runtime)
(import-from .Noodle.runtime _items)

(= parenmap {')':'(' ']':'[' '}':'{'})

(define (get-user-expression sofar:'' prompt:'>> ')
    (= sofar (.'\n'.join \(sofar (raw_input prompt))))
    (= quotes-on False)
    (= in-comment False)
    (= parenstack [])
    (= escaped False)
    (for c in sofar
        (cond (escaped
                  (= escaped False))
              (quotes-on
                  (cond ((== c '\\')
                         (= escaped True))
                        ((== c quotes-on)
                         (toggle quotes-on))))
              (in-comment
                  (if (== c '\n')
                      (toggle in-comment)))
              ((in c (.parenmap.values))
                  (.parenstack.append c))
              ((in c (.parenmap.keys))
                  (if (== 0 (len parenstack))
                      (raise (.Noodle.error.NoodleSyntaxError
                                  (% "mismatched %c" c))))
                  (if (!= (.parenstack.pop) [parenmap c])
                      (raise (.Noodle.error.NoodleSyntaxError
                                  (% "mismatched %c" [parenmap c])))))
              ((in c \('"' "'"))
                  (= quotes-on c))
              ((== c '#')
                  (= in-comment True))))
    (if parenstack
        (get-user-expression sofar:sofar prompt:'.. ')
        sofar))

(define (print-result value)
    (if (is-not None value) (print (repr value))))

(define (read-eval-print-loop env)
    (while True
        (print-result
            (try
                (= [env '_']
                   (nu-eval-str
                       (try
                           (get-user-expression)
                         (except (EOFError)
                           (print) (break))
                         (except (.Noodle.error.NoodleSyntaxError e)
                           (.sys.stderr.write (% "Syntax error: %s\n" (str e)))
                           (continue))
                         (except (.Noodle.error.NoodleScannerError e)
                           (.sys.stderr.write (% "Scanner error: %s\n" (str e)))
                           (continue)))
                       env
                       None
                       '*stdin*'))
              (except ()
                (import traceback)
                (= (t v tb) (.sys.exc_info))
                # strip off this func:
                (= tb .tb.tb_next)
                (.traceback.print_exception t v tb file:.sys.stderr)
                None)))))

(define (main)
    (try (import readline)
        (except (ImportError)))
    (let ((env (._items.copy)))
        (.env.update {'__builtins__': (import __builtin__)
                      '__name__': '__main__'})
        (read-eval-print-loop env)))

(if (== __name__ '__main__') (main))
