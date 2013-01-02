# try-finally:

(= o (set))
(try
  (try (raise (Exception "too much!"))
    (finally (.o.add "good")))
  (except (Exception) (.o.add "great")))
(assert (in "good" o))
(assert (in "great" o))
