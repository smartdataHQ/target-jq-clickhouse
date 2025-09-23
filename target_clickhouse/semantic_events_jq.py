def semantic_events_jq_expression() -> str:
    return """
[.[] |
 { 
  type: ("track" | tostring),
  event: ("order_purchased" | tostring), 
  timestamp: (.customer__created_at),

  flags: {
    taxes_included:          .taxes_included,
    test:                    .test,
    buyer_accepts_marketing: .buyer_accepts_marketing,
    tax_exempt:              .tax_exempt
  },

  "commerce.products.line_id": ([.line_items[] | .id | tostring]),
  "commerce.products.product_id": ([.line_items[] | .product_id | tostring]),
  "commerce.products.product": ([.line_items[] | .title]),
  "commerce.products.brand": ([.line_items[] | .vendor]),
  
  partition: ("shopify.com" | tostring),
  sign: ("1" | tonumber)
 }
]
"""