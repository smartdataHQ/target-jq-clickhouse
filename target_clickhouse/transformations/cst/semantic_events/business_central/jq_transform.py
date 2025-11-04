def jq_transform() -> str:
    return r"""
[.[] |
 { 
  entity_gid: (.company_id | tostring),
  type: ("track" | tostring),
  event: ("sales_invoices" | tostring), 
  timestamp: (.invoiceDate),

  location: [
    {
      "location_of": "shipping_address",
      "label": .shipToName,
      "street": (.sellToAddressLine1 | tostring),
      "region": (.sellToCity | tostring),
      "postal_code": (.sellToPostCode | tostring),
      "country": (.sellToCountry | tostring),
      "longitude": (.shipping_address__longitude // 0.0 | tonumber),
      "latitude": (.shipping_address__latitude // 0.0 | tonumber)
    },
    {
      "location_of": "billing_address",
      "label": .billToName,
      "street": (.billToAddressLine1 | tostring),
      "region": (.billToCity | tostring),
      "postal_code": (.sellToPostCode | tostring),
      "country": (.billToCountry | tostring),
      "longitude": (.shipping_address__longitude // 0.0 | tonumber),
      "latitude": (.shipping_address__latitude // 0.0 | tonumber)
    }
  ],

  "traits.id":  (.customerId | tostring),
  "traits.name":  ((.customerName // null) + (.customer__last_name | " " + .) | tostring),
  "traits.email":  (.email | tostring),
  "traits.phone":  (.phoneNumber | tostring),

  properties: ({    
    invoice_number: (.number // "" | tostring)
  }),

  dimensions: {
    status: (.status | tostring)
  },
  
  metrics: {
    remaining_amount: (.remainingAmount | tonumber)
  },

  flags: ({
    prices_include_tax: (.pricesIncludeTax),
    discount_applied_before_tax: (.discountAppliedBeforeTax)
  }), 

  "commerce.checkout_id": (.paymentTermsId | tostring),
  "commerce.revenue": (.totalAmountExcludingTax | tonumber),
  "commerce.tax": (.totalTaxAmount | tonumber),
  "commerce.discount": (.discountAmount | tonumber),
  "commerce.currency": (.currencyCode | tostring),

  "commerce.products": [
    .salesInvoiceLines[]
    | {
        line_id: (.id | tostring),
        product_id: (.itemId | tostring),
        product: (.description | tostring),
        units: (.quantity | tonumber),
        unit_price: (if (.quantity|tonumber) != 0 then (.amountExcludingTax|tonumber) / (.quantity|tonumber) else 0 end),
        unit_cost: (if (.quantity|tonumber) != 0 then (.amountIncludingTax|tonumber) / (.quantity|tonumber) else 0 end),
        uom: (.unitOfMeasureCode | tostring),
        tax_percentage: (.taxPercent | tonumber),
        discount_percentage: (.discountPercent | tonumber)
      }
  ],

  event_gid: (.id | tostring),
  partition: (.company_name | ascii_downcase | gsub("\\s+"; ".")),
  sign: ("1" | tonumber)
  }
]
"""