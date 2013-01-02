# raw strings

(assert (== r"foo\nbar" "foo\\nbar"))
(assert (== (.r'''    string with spaces\''' ending'''.strip)
            "string with spaces\\''' ending"))
(assert (== ur'moo\'' u"moo\\'"))
