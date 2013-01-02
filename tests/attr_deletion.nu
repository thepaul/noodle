# deletion of attributes

(define some-object ((anon-class (object))))
(= .some-object.twinkie 'yum')
(assert (hasattr some-object 'twinkie'))
(del .some-object.twinkie)
(assert (not (hasattr some-object 'twinkie')))
