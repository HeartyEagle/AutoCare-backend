from io import StringIO
import pandas as pd
import bcrypt
from passlib.context import CryptContext

# Function to hash a password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    '''Hashes a password using bcrypt'''
    return pwd_context.hash(password)


# Read the CSV data
# If you have the CSV file saved, replace 'user_data.csv' with the file path
# For demonstration, I'll use the provided data as a string
csv_data = """user_id,name,username,password,phone,email,address,discriminator
1,John Doe,johndoe,hashedpass123,1234567890,john@example.com,123 Main St,customer
2,Jane Smith,janesmith,hashedpass456,0987654321,jane@example.com,456 Oak Ave,staff
3,Admin User,adminuser,hashedpass789,1122334455,admin@example.com,789 Pine Rd,admin
4,Mike Johnson,mikej,hashedpass012,2233445566,mike@example.com,321 Elm St,customer
5,Tom Brown,tomb,hashedpass345,3344556677,tom@example.com,654 Cedar Ln,staff
6,Alice Green,aliceg,hashedpass678,4455667788,alice@example.com,987 Birch Rd,customer
7,Bob Wilson,bobw,hashedpass901,5566778899,bob@example.com,147 Maple Dr,staff
8,Emma Davis,emmad,hashedpass234,6677889900,emma@example.com,258 Willow St,customer
9,David Clark,davidc,hashedpass567,7788990011,david@example.com,369 Spruce Ave,staff
10,Lisa White,lisaw,hashedpass890,8899001122,lisa@example.com,741 Ash Ln,customer
11,Mark Taylor,markt,hashedpass111,9900112233,mark@example.com,852 Poplar Rd,staff
12,Sarah Lee,sarahl,hashedpass222,1011123344,sarah@example.com,963 Linden St,customer
13,James Miller,jamesm,hashedpass333,1122335566,james@example.com,159 Cherry Dr,staff
14,Anna Harris,annah,hashedpass444,2233446677,anna@example.com,267 Magnolia Ave,customer
15,Chris Evans,chrise,hashedpass555,3344557788,chris@example.com,378 Laurel Rd,staff"""

# Convert the string data to a pandas DataFrame
df = pd.read_csv(StringIO(csv_data))

# Hash the passwords (assuming original password = username)
df['password'] = df['username'].apply(get_password_hash)

# Write the updated DataFrame to a new CSV file
output_file = 'updated_user_data.csv'
df.to_csv(output_file, index=False)

print(f"Updated CSV file has been written to {output_file}")
print("\nFirst few rows of the updated DataFrame:")
print(df.head())
