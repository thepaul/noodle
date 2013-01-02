# assigning to attributes

(= empty-object ((class nothing)))
(= .empty-object.first-attribute (nothing))
(assert (==
           (= .empty-object.first-attribute.another-attr \(1))
           \(1)))
(assert (== .empty-object.first-attribute.another-attr \(1)))
