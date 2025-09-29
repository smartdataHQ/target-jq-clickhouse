def semantic_events_jq_expression() -> str:
    return """
[.[] |
 { 
  entity_gid: ("https://shopify.com/orders"),
  type: ("track" | tostring),
  event: ("order_purchased" | tostring), 
  timestamp: (.customer__created_at),

  location: [{
    "location_of": "shipping_address",
    "label": "address",
    "street": (.shipping_address__address1 | tostring),
    "region": (.shipping_address__city | tostring),
    "postal_code": (.shipping_address__zip | tostring),
    "country": (.shipping_address__country | tostring),
    "longitude": (.shipping_address__longitude // 0.0 | tonumber),
    "latitude": (.shipping_address__latitude // 0.0 | tonumber)
  }],

  "traits.id":  (.customer__id | tostring),
  "traits.name":  ((.customer__first_name // null) + (.customer__last_name | " " + .) | tostring),
  "traits.first_name":  (.customer__first_name | tostring),
  "traits.last_name":  (.customer__last_name | tostring),
  "traits.email":  (.customer__email | tostring),
  "traits.phone":  (.customer__phone | tostring),
  "traits.address":  ({
      street:        (.customer__default_address__address1 | tostring),
      city:          (.customer__default_address__city | tostring),
      postalCode:    (.customer__default_address__zip | tostring),
      country:       (.customer__default_address__country | tostring),
      country_code:  (.customer__default_address__country_code | tostring),
      province:      (.customer__default_address__province | tostring),
      province_code: (.customer__default_address__province_code | tostring)
    }),

  properties: ({    
    cart_token: (.cart_token // "" | tostring),
    checkout_token: (.checkout_token // "" | tostring),
    order_status_url: (.order_status_url | tostring),
    confirmation_number: (.confirmation_number | tostring)
  }),

  dimensions: {
    source_name: (.source_name | tostring),
    financial_status: (.financial_status | tostring),
    fulfillment_status: (.fulfillment_status | . // "unfullfilled" | tostring)
  },

  metrics: {
    total_line_items_price: (.total_line_items_price | tonumber),
    total_weight:           (.total_weight           | tonumber),
    total_tip_received:     (.total_tip_received     | tonumber),
  },

  flags: ({
    test:                     (.test),
    confirmed:                (.confirmed), 
    customer_address_default: (.customer__default_address__default),
    email_verified:           (.customer__verified_email),
    taxes_included:           (.taxes_included),
    buyer_accepts_marketing:  (.buyer_accepts_marketing),
    tax_exempt:               (.tax_exempt)
  }), 

  "commerce.checkout_id": (.checkout_id | tostring),
  "commerce.order_id": (.order_number | tostring),
  "commerce.external_order_id": (.order_number | tostring),
  "commerce.revenue": (.total_price | tonumber),
  "commerce.tax": (.total_tax | tonumber),
  "commerce.coupon": (
      if .discount_applications != [] then
        (.discount_applications[] | select(.target_selection=="all") | .code | tostring)
      else "NULL" end
    ),
  "commerce.discount": (.total_discounts | tonumber),
  "commerce.currency": (.currency | tostring),

  "commerce.products": [
    .line_items[]
    | {
        line_id: (.id | tostring),
        product_id: (.product_id | tostring),
        sku: (.sku | tostring),
        product: (.title | tostring),
        brand: (.vendor | tostring),
        variant: (.variant_title | tostring),
        units: (.quantity | tonumber),
        unit_price: (.price | tonumber),
        tax_percentage: (.tax_lines[] // {} | .rate // 0 | tonumber),
        discount_percentage: ((.discount_allocations[0] | .amount // 0 | tonumber) / (.price | tonumber) * 100)
      }
  ],

  event_gid: ("https://shopify.com/order/" + (.id | tostring)),
  partition: ("shopify.com" | tostring),
  sign: ("1" | tonumber)
 }
]
"""