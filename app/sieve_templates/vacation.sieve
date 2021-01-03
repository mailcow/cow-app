require ["vacation","date","relational"];
if allof ( currentdate :value "ge" "date" "2021-01-02", currentdate :value "le" "date" "2021-01-10" ) {
vacation
:days 7
:addresses ["user3@deneme.com"]
text:
Bu bir otomatik dönüttür.
.
;
}
