# slices

(assert (== [(range 20) 0:9:2] \[0 2 4 6 8]))
(assert (== [(mktuple 5 4 3 2 1) 3:1:-1] \(2 3)))

(assert (== [(range 10 35 4) :4] \[10 14 18 22]))
(assert (== [(range 10 1 -1) 4:] \[6 5 4 3 2]))

(= marklar \[2 3 4 'marklar'])
(= marklar-of-marklar marklar)
(= copy [marklar :])

(= [marklar-of-marklar 1] 100)
(assert (== marklar \[2 100 4 'marklar']))
(= [copy 2] 200)
(assert (== copy \[2 3 200 'marklar']))
(assert (== marklar \[2 100 4 'marklar']))
