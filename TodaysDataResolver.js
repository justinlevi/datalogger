#set( $todayFormatted = $util.time.nowFormatted("yyyy-MM-dd HH:mm:ssZ", "-04:00").substring(0, 10) + " 00:00:00+0000" )
#set( $todayMilliSecondsTimestamp = $util.time.parseFormattedToEpochMilliSeconds($todayFormatted, "yyyy-MM-dd HH:mm:ssZ") )
#set( $todaySecondsTimestamp = $util.time.epochMilliSecondsToSeconds($todayMilliSecondsTimestamp) )
{
    "version" : "2017-02-28",
    "operation" : "Query",
    "query" : {
        "expression": "deviceID = :deviceID AND #date > :todaySecondsTimestamp",
        "expressionNames": {
        	"#date": "date"
        },
        "expressionValues" : {
            ":deviceID" : $util.dynamodb.toDynamoDBJson($ctx.args.deviceID),
            ":todaySecondsTimestamp" : {
              "N": $todaySecondsTimestamp
            }
        }
    },
    "scanIndexForward": #if( $context.args.sortDirection )
        #if( $context.args.sortDirection == "ASC" )
            true
        #else
            false
        #end
      #else
          true
    #end,
    "index" : "deviceID-date-index",
    "nextToken" : $util.toJson($util.defaultIfNullOrEmpty($ctx.args.nextToken, null)),
    "limit" : $util.defaultIfNull($context.args.limit, 10),
    "consistentRead" : false,
    "select" : "ALL_ATTRIBUTES",
    "filter" : #if($context.args.filter) $util.transform.toDynamoDBFilterExpression($ctx.args.filter) #else null #end,
}
