# for-list (list comprehensions)

(assert (== \[1 2 3 4 21]
            (for-list a in \[0 1 2 3 20]
                      (+ a 1))))

(assert (== \[\[0 3 6] \[1 4 7] \[2 5 8]]
            (for-list (a b c) in (zip \[0 1 2] \[3 4 5] \[6 7 8])
                      \[a b c])))
