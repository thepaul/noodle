(assert (is

# comment call (essentially the same as (if 0 ...), but doesn't make the
# compiled code any bigger)
(comment """This is a comment. It shouldn't do anything.. but note it has
         to be syntactically correct. We can't just put arbitrary stuff
         in here, unless we surround it with quotes."""

         Note (comment) does leave a value behind- everything has to leave
         a value behind
)

None))
