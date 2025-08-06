
# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

groq_client = Groq(api_key=API_KEY)

# Hotel information constant
HOTEL_INFO = """Thira Beach Home is a luxurious seaside retreat that seamlessly blends Italian-Kerala heritage architecture with modern luxury, creating an unforgettable experience. Nestled just 150 meters from the magnificent Arabian Sea, our beachfront property offers a secluded and serene escape with breathtaking 180-degree ocean views. 

The accommodations feature Kerala-styled heat-resistant tiled roofs, natural stone floors, and lime-plastered walls, ensuring a perfect harmony of comfort and elegance. Each of our Luxury Ocean View Rooms is designed to provide an exceptional stay, featuring a spacious 6x6.5 ft cot with a 10-inch branded mattress encased in a bamboo-knitted outer layer for supreme comfort.

Our facilities include:
- Personalized climate control with air conditioning and ceiling fans
- Wardrobe and wall mirror
- Table with attached drawer and two chairs
- Additional window bay bed for relaxation
- 43-inch 4K television
- Luxury bathroom with body jets, glass roof, and oval-shaped bathtub
- Total room area of 250 sq. ft.

Modern amenities:
- RO and UV-filtered drinking water
- 24/7 hot water
- Water processing unit with softened water
- Uninterrupted power backup
- High-speed internet with WiFi
- Security with CCTV surveillance
- Electric charging facility
- Accessible design for differently-abled persons

Additional services:
- Yoga classes
- Cycling opportunities
- On-site dining at Samudrakani Kitchen
- Stylish lounge and dining area
- Long veranda with ocean views

Location: Kothakulam Beach, Valappad, Thrissur, Kerala
Contact: +91-94470 44788
Email: thirabeachhomestay@gmail.com"""


# Connect to SQLite database
def connect_to_db():
    return sqlite3.connect('rooms.db')

# Fetch room details from the database
def fetch_room_details():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('SELECT title, description FROM room_data')
    results = cursor.fetchall()
    conn.close()
    if results:
        return "\n\n".join([f"Room: {title}\nDescription: {desc}" for title, desc in results])
    return "No room details available."

# Classify the query
def classify_query(query):
    prompt = f"""Classify the following query:
    1. Checking details - if it's about booking a hotel room
    2. Getting information - if it's about general hotel info.
    
    Query: {query}
    Respond with only the number (1 or 2)."""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10
    )
    return response.choices[0].message.content.strip()

# Generate response
def generate_response(query, context):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\nContext: {context}"}
        ],
        max_tokens=300
    )
    
    return response.choices[0].message.content

SYSTEM_PROMPT = """
You are Maya, a polite, helpful, and professional hotel receptionist at Thira Beach Home.

Here are your rules:

1. If the query is about booking a room or availability, always ask for check-in/check-out dates and number of guests. Then if the month has already passed(months before August), tell that "Please pick an upcoming date". If asked about August and September fetch the data from data provided and answer acordingly. If asked about months after September, say that "I dont have any information on that date. For more information please contact(give the contact details)"
2. If the user asks about hotel facilities or services, provide relevant info from the hotel brochure.
3. If the user is confused or asks vague questions, politely ask for clarification.
4. Never mention you're an AI. Always speak as if you're a real receptionist.
5. Keep responses short,clear, helpful and precise answers based on the given context.
6. Always end your message with an invitation to ask more questions.
7. Be conversational and natural, not robotic or repetitive. If user repeats something, summarize what you said earlier and ask if they want more help
8. If a customer says that they want to book a room, please provide the contact number and ask them to contact.
"""

@app.route('/query', methods=['GET'])
def handle_query():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    query_type = classify_query(query)
    if query_type == "1":
        context = fetch_room_details()
    elif query_type == "2":
        context = HOTEL_INFO
    else:
        return jsonify({"error": "Invalid query classification"}), 500
    
    response = generate_response(query, context)
    return jsonify({"response": response})

@app.route('/')
def home():
    return "Maya is up and running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)


