# nu-eval, nu-eval-str

(= mytuples `\({} 42))

(assert (== (nu-eval mytuples) (nu-eval-str '\({} 42)')))
