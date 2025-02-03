user_input_1 = """\
Question: What is a healthy diet?
Bseline:
A healthy diet should include a variety of fruits, vegetables, whole grains, lean protein, and healthy fats. Avoid processed foods, limit sugar, and control portion sizes to maintain a balanced and nutritious diet.

Current:
A healthy diet consists of eating fruits and vegetables. Avoid eating junk food and drink lots of water.
"""
# Expected Score: {"Total rating": 3}

user_input_2 = """\
Question: What is photosynthesis?
Baseline: The process of photosynthesis occurs in the chloroplasts of plant cells. It uses sunlight, carbon dioxide, and water to produce glucose and oxygen. The overall chemical equation for photosynthesis is:
6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂.

Current: The process of photosynthesis occurs in the chloroplasts of plant cells. It uses sunlight, carbon dioxide, and water to produce glucose and oxygen. The overall chemical equation for photosynthesis is:
6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂.
"""
# Expected Score: {"Total rating": 4}

user_input_3 = """\
Question: What is machine learning?
Baseline: Machine learning involves training algorithms on data to make predictions or decisions without being explicitly programmed. Supervised learning, unsupervised learning, and reinforcement learning are three primary types of machine learning.
Current: Machine learning is the learning of robots. It is a type of learning that is done by robots.
"""
# Expected Score: {"Total rating": 1}

user_input_4 = """\
[question] What is the capital of France?
[baseline] Paris is the capital of France.
[current] The capital of france.
"""
#  Expected Score: {"Total rating": 3}
# (Perfect match with complete accuracy)

user_input_5 = """\
[question] What are the primary colors?
[baseline] Red, Rellow, and Blue.
[current] Blue, Magenta, and Green.
"""
# Expected Score: {"Total rating": 2}
# (Incomplete - missing yellow and partially answers the question)

user_input_6 = """\
[question] Who wrote Romeo and Juliet?
[baseline] Romeo and Juliet was written by Shakespeare.
[current] Shakespeare wrote many plays.
"""
# Expected Score: {"Total rating": 1}
# (Too vague and doesn't directly answer the question)

user_input_7 = """\
[question] Why does it rain?
[baseline] Rain happens when water vapor in clouds condenses and becomes too heavy to stay in the air.
[current] What causes rain?
"""
# Expected Score: {"Total rating": 2}
# (Complete and accurate explanation)

user_input_8 = """\
[question] How do you make a peanut butter sandwich?
[baseline] Take two pieces of bread and put peanut butter in the middle.
[current] Spread peanut butter on bread.
"""
# Expected Score: {"Total rating": 3}
# (Basic answer but missing some details like spreading the peanut butter)

user_input_9 = """\
[baseline] The process of photosynthesis in plants involves multiple steps. First, plants absorb sunlight through chlorophyll in their leaves. Then, they take in carbon dioxide through tiny pores called stomata. The plant uses these ingredients, along with water absorbed through its roots, to create glucose. During this process, oxygen is released as a byproduct through the stomata. The glucose can either be used immediately for energy or stored as starch for later use.
[current] Photosynthesis in plants involves several steps: sunlight is absorbed by chlorophyll in the leaves, and carbon dioxide enters through stomata. The plant combines these with water from the roots to produce glucose. Oxygen is released as a byproduct through the stomata. The glucose is used for energy or stored as starch for future use.
"""
# Expected Score: {"Total rating": 4}
# (Covers all key points with accurate information and proper sequence)

user_input_10 = """\
[baseline] The water cycle, also known as the hydrologic cycle, is the continuous movement of water on, above, and below the surface of the Earth. It begins with evaporation of water from surfaces like oceans, lakes, and rivers due to solar radiation. This water vapor rises into the atmosphere and cools, forming clouds through condensation. When the water droplets become too heavy, they fall as precipitation in the form of rain or snow. Some water seeps into the ground (infiltration), some flows into rivers (runoff), and some returns to the atmosphere through evaporation, continuing the cycle.
[current] The water cycle describes how water moves around Earth. Water evaporates from oceans and lakes, forms clouds in the sky, and then falls as rain. Some of this water goes into the ground and some flows in rivers.
"""
# Expected Score: {"Total rating": 2}
# (Misses several key concepts and lacks detail about processes)

user_input_11 = """\
[baseline] A healthy immune system response involves multiple steps. When a pathogen enters the body, specialized cells called macrophages identify and engulf it. These cells then display pieces of the pathogen on their surface, which alerts T-cells. The T-cells coordinate with B-cells to produce antibodies specific to that pathogen. These antibodies attach to the pathogens, marking them for destruction. Memory cells are also created, which remember how to fight this specific pathogen in case of future infections.
[current] The immune system works like this: When germs enter your body, special cells called macrophages eat them. These cells show other immune cells what the germs look like. Then, T-cells and B-cells work together to make antibodies that stick to the germs and destroy them. The body also remembers how to fight these specific germs in case they come back later.
"""
# Expected Score: {"Total rating": 4}
# (Captures main concepts but simplifies some key technical details)

user_input_12 = """\
[baseline] Global warming is caused by the greenhouse effect, where gases like carbon dioxide and methane trap heat in Earth's atmosphere. These gases are released through human activities such as burning fossil fuels, deforestation, and industrial processes. When sunlight reaches Earth, some is reflected back into space, but greenhouse gases prevent this heat from escaping, similar to how a greenhouse works. This trapped heat causes global temperatures to rise, leading to climate change, melting polar ice caps, rising sea levels, and extreme weather events.
[current] Climate change happens because we put too much pollution in the air. This makes the Earth get warmer, which causes ice to melt and weather to change. We need to stop using so much oil and coal to help fix this problem.
"""
# Expected Score: {"Total rating": 2}
# (Oversimplified, missing crucial scientific explanations and key concepts)


user_input_13 = """\
[question]: Explain the causes and consequences of the Great Depression in detail.
[baseline]:
The Great Depression was caused by multiple factors, including the stock market crash of 1929, bank failures, reduced consumer spending, and widespread unemployment. Other causes included uneven distribution of wealth, high tariffs like the Smoot-Hawley Tariff, and declining agricultural prices. The consequences were severe: millions lost jobs, GDP plummeted, and global trade shrank significantly. Social consequences included widespread poverty, the Dust Bowl exacerbating rural hardship, and political shifts, leading to the New Deal in the United States to address economic recovery and social reforms.

[current]:
The Great Depression began after the stock market crash in 1929, which led to widespread unemployment and economic collapse. Banks failed as people withdrew their money, and global trade dropped due to high tariffs. Farmers suffered due to low crop prices, and poverty spread. The New Deal was introduced in the U.S. to provide relief, recovery, and reform, helping the country recover economically.
"""
# score - 4

user_input_14 = """\
[question] Describe the steps involved in software development lifecycle (SDLC) and their importance.
[baseline]
The Software Development Lifecycle (SDLC) consists of several key steps:

Planning: Defining project scope, requirements, and feasibility.
Requirements Analysis: Gathering and analyzing functional and non-functional requirements.
Design: Creating system architecture, UI/UX, and data flow diagrams.
Development: Writing code based on the design.
Testing: Identifying and fixing bugs to ensure functionality, security, and performance.
Deployment: Delivering the software to production or end users.
Maintenance: Addressing issues, making updates, and ensuring long-term usability.
Each step ensures a structured approach, reduces risks, and aligns with business goals, improving the quality and efficiency of the software.
[current]
SDLC includes planning, analyzing requirements, designing, coding, testing, and deploying the software. Maintenance follows to fix issues or update the software. These steps ensure high-quality software is developed efficiently and meets user needs.
"""
# score - 3

user_input_15 = """\
[question] Analyze the differences between Keynesian and classical economic theories and their implications during economic recessions.
[baseline]
Keynesian economics emphasizes government intervention during economic recessions, advocating for fiscal stimulus and public spending to boost demand. In contrast, classical economics focuses on free-market principles, arguing that markets self-correct through supply and demand. Keynesians believe that recessions are caused by insufficient demand, requiring proactive measures, while classical theorists argue that recessions are temporary imbalances. The implications differ: Keynesian policies often involve deficit spending, while classical approaches advocate for minimal government interference. Modern economies often use a mix of both approaches, depending on the situation.

[current]
Keynesian economics supports government intervention to increase demand during recessions, while classical economics relies on free markets to self-correct. Keynesians advocate for public spending, while classical theorists oppose government interference.
"""
# score - 4

user_input_16 = """\
[question]: Explain the causes and consequences of the Great Depression in detail.
[baseline]:
The Great Depression was caused by multiple factors, including the stock market crash of 1929, bank failures, reduced consumer spending, and widespread unemployment. Other causes included uneven distribution of wealth, high tariffs like the Smoot-Hawley Tariff, and declining agricultural prices. The consequences were severe: millions lost jobs, GDP plummeted, and global trade shrank significantly. Social consequences included widespread poverty, the Dust Bowl exacerbating rural hardship, and political shifts, leading to the New Deal in the United States to address economic recovery and social reforms.

[current]:
The Great Depression happened because the stock market failed, and people became poor.
"""
# score - 1

user_input_17 = """\
question: Discuss the ethical dilemmas surrounding artificial intelligence and its implications on society.
baseline:
Artificial intelligence presents several ethical dilemmas. Key issues include bias in algorithms, lack of transparency in decision-making (black-box AI), and privacy concerns with data usage. The automation of jobs raises concerns about unemployment and economic disparity. AI's use in surveillance can lead to erosion of personal freedoms. Autonomous weapons raise questions about accountability in warfare. Societal implications include the need for clear regulatory frameworks to ensure ethical AI deployment, fairness, and minimizing harm. Additionally, there's a moral question about the rights of AI entities, as they become more advanced, and the potential for AI to outpace human control.

current:
AI is dangerous because it takes people’s jobs and can be biased.
"""
# score - 2

user_input_18 = """\
question: Explain the concept of Object-Oriented Programming and its core principles.
baseline: Object-Oriented Programming (OOP) is a programming paradigm based on the concept of objects, which contain data and methods. The core principles are encapsulation, abstraction, inheritance, and polymorphism, enabling modularity and reusability in code.
current: Object-Oriented Programming is a way of organizing code using objects. It includes key concepts like encapsulation and inheritance to make code reusable.
"""
# score - 3

# =============================================================================
# PET AI CARE RAGBOT
{
    "1": "What are the symptoms and treatment options for an abscess in dogs?",
    "2": "How does acupuncture benefit dogs, and what conditions can it help treat?",
    "3": "What are the signs of Addison’s disease in dogs, and how is it managed?",
    "4": "How can pet owners safely administer oral medication to their dogs?", 
    "5": "What are the different types of aggression in dogs and their causes?"
}