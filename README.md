# Secure Web App: Feedback Collection System

This project is an implementation of a secure web application that allows citizens to submit feedback or complaints about road conditions in Addis Ababa City. The application mitigates common web security vulnerabilities, providing a safe and secure platform for its users.

## Features

1. **Signup and Login:** Users can register and login to the application. The system securely manages user data and sessions.
2. **Dashboard:** Upon login, users are directed to a dashboard where they can submit new feedback and view their past feedbacks.
3. **Feedback Submission:** Users can submit feedback including their name, email, comment, and optionally upload a file (PDF format) if the comment is extensive.
4. **Review Feedback:** Users can review their previously submitted feedbacks and edit the content or replace the attached PDF file.
5. **Moderator Page:** A special page is accessible for admins to monitor user activities. They can disable users' accounts and have the privilege to view all feedbacks from the users.

## Security Measures

The application is designed to protect against most common web vulnerabilities, which includes:

1. **Authentication, Authorization, and Session Management:** The app securely manages user sessions and implements proper authorization checks to prevent unauthorized access.

2. **Code Execution Prevention:** Measures are put in place to prevent both remote and local code execution vulnerabilities.

3. **Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF) Prevention:** The app implements measures to mitigate XSS and CSRF attacks.

4. **SQL Injection Prevention:** The app uses SQLAlchemy ORM for database interactions which provides inherent protection against SQL Injection attacks.

5. **Input Validation:** All user inputs are properly validated and sanitized to avoid security risks.

6. **Anti-Automation:** To prevent bot activities and spamming, anti-automation techniques are utilized.

7. **Honey Pot:** Honey Pot is implemented to distract attackers and analyze their activities.

8. **Safe Redirection:** The app ensures safe redirection, preventing Open Redirect vulnerabilities.

## Prerequisites

1. Python 3.6+
2. Flask 1.1+
3. SQLAlchemy 1.4+

## Getting Started

1. Clone the repository.
2. Navigate to the project directory.
3. Install required dependencies using `pip install -r requirements.txt`.
4. Run the application using `flask run`.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
