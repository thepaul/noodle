# lambda usage

(= my-list \[0 1 2 3])

(assert (== ((lambda (arg1 arg2) (.arg1.append "foobar") arg2)
             my-list
             "the result")
            "the result"))
(assert (== my-list \[0 1 2 3 'foobar']))
