#foreach( $item in $ctx.result.items )
  #set( $epochMillis = (${item.date} * 1000))
  ## #set( $date = $util.time.epochMilliSecondsToISO8601($epochMillis))
  #set( $date = $util.time.epochMilliSecondsToFormatted($epochMillis, "yyyy-MM-dd HH:mm:ss", "-04:00") )
  $util.qr($item.put("dateFormatted", ${date}))
#end

$util.toJson($ctx.result)
