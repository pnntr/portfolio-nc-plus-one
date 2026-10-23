# NOTES

## Decisions taken

### asyncpg over psycopg2
asyncpg is built natively for async work whereas psycopg2 is not. This system is mostly 
IO or database compute bound so an async design should perform better.

### argon2 over brypt
argon2 is the a more secure variant of hash as it is not only CPU bound, like bryct, 
but also memory bound. This makes argon2 harder to to crack with specialised hardware.

### jwt expiry

###
