WITH original AS (
    SELECT *, email AS original_email
    FROM {{ source('mongo_mongousers', 'raw') }}
)
SELECT
    _id,
    email,
    original_email,
    sha256(concat(email, 'your_salt_value_here')) AS salted_hashed_email,
    name,
    age
FROM original
