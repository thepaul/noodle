# class

(class (DictExtender (dict))
  """class that wraps a dict but also allows attribute (".foo.bar")
  access to items.
  """

  (define (__init__ self)
    (.dict.__init__ self))

  (= __getattr__ .dict.__getitem__))

(= d-e (DictExtender))
(.d-e.setdefault 'key' 'value')
(assert (== .d-e.key 'value'))

(define (make-closure-class arg)
  (class closure-class
    (define attribute arg))
  closure-class)
(assert (== .(make-closure-class 91).attribute 91))
