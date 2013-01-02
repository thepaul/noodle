#!/usr/bin/noodle

(import Noodle)
(import nudoc)

(= childfiles
   \("intro"
     "macros"))

(= children (map .nudoc.read childfiles))

(parse-docs
  (section name:"header"
    (doctitle "Noodle Tutorial")
    (docauthor "paul cannon <paul@nafpik.com")
    (span klass:"releaseinfo" "Noodle " .Noodle.version))

  (section name:"contents"
    (itemlist
      @(for-list child in children
         (item klass:"childcontents"
           (link target:.childdoc.address .childdoc.title)
           (.childdoc.contents)))))

  (section name:"footer"
    (copyright "Copyright " .nudoc.entity.copy " 2006 by paul cannon"
               "<paul@nafpik.com>.")))
