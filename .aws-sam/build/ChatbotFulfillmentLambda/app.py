"""
AWS Lambda Function for Amazon Lex V2 Fulfillment with Bedrock Knowledge Base Integration

This function serves as the fulfillment hook for Amazon Lex V2 chatbot.
It handles basic intents directly and uses Amazon Bedrock Knowledge Base
for unrecognized user input via FallbackIntent.

Author: Senior Python Developer
Runtime: Python 3.10
"""

import json
import os
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
bedrock_client = boto3.client('bedrock-agent-runtime')
dynamodb = boto3.resource('dynamodb')

# Environment Variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'SessionTable')
KNOWLEDGE_BASE_ID = os.environ.get('KB_ID', '')
# AWS_REGION is automatically available in Lambda environment
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize DynamoDB table
table = dynamodb.Table(TABLE_NAME)


def get_session(session_id):
    """
    Retrieve session data from DynamoDB table by session_id.
    
    Args:
        session_id (str): The unique session identifier
        
    Returns:
        dict: Session data or empty dict if not found or error occurs
    """
    try:
        response = table.get_item(Key={'session_id': session_id})
        session_data = response.get('Item', {})
        print(f"Retrieved session data for {session_id}: {session_data}")
        return session_data
    except ClientError as e:
        print(f"Error retrieving session {session_id}: {e.response['Error']['Message']}")
        return {}
    except Exception as e:
        print(f"Unexpected error retrieving session {session_id}: {str(e)}")
        return {}


def save_session(session_id, session_data):
    """
    Save session data to DynamoDB table.
    
    Args:
        session_id (str): The unique session identifier
        session_data (dict): The session data to save
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        # Ensure session_id is included in the data
        session_data['session_id'] = session_id
        
        table.put_item(Item=session_data)
        print(f"Session {session_id} saved successfully")
        return True
    except ClientError as e:
        print(f"Error saving session {session_id}: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"Unexpected error saving session {session_id}: {str(e)}")
        return False


def close(session_attributes, fulfillment_state, message_content):
    """
    Format the JSON response to send back to Amazon Lex V2.
    
    Args:
        session_attributes (dict): Session attributes to maintain state
        fulfillment_state (str): The fulfillment state (e.g., 'Fulfilled', 'Failed')
        message_content (str): The message content to send to the user
        
    Returns:
        dict: Properly formatted Lex V2 response
    """
    return {
        'sessionState': {
            'sessionAttributes': session_attributes if session_attributes else {},
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': 'FallbackIntent',
                'state': fulfillment_state
            }
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': message_content
            }
        ]
    }


def query_local_kb(text):
    """
    Comprehensive local knowledge base for AWS services (fallback when Bedrock is not available).
    Returns detailed information about AWS services based on keywords.
    """
    text_lower = text.lower()
    
    # Compute Services
    if 'lambda' in text_lower and 'edge' not in text_lower:
        return "AWS Lambda is a serverless, event-driven compute service that lets you run code without provisioning or managing servers. You pay only for the compute time consumed. Lambda automatically scales from a few requests per day to thousands per second. It supports multiple programming languages including Python, Node.js, Java, Go, Ruby, and .NET. Common use cases include API backends, data processing, real-time file processing, and IoT backends."
    
    elif 'ec2' in text_lower or 'elastic compute cloud' in text_lower:
        return "Amazon EC2 (Elastic Compute Cloud) provides secure, resizable compute capacity in the cloud. Choose from 500+ instance types optimized for different workloads: general purpose (T3, M5), compute optimized (C5, C6g), memory optimized (R5, X1), storage optimized (I3, D2), and accelerated computing (P3, G4). Features include Auto Scaling, Elastic Load Balancing, Amazon EBS volumes, and multiple purchase options (On-Demand, Reserved, Spot)."
    
    elif 'ecs' in text_lower or 'elastic container service' in text_lower:
        return "Amazon ECS (Elastic Container Service) is a fully managed container orchestration service that makes it easy to deploy, manage, and scale containerized applications. It supports Docker containers and works seamlessly with AWS Fargate for serverless compute, or EC2 for full control. ECS integrates with other AWS services like ELB, CloudWatch, and IAM for a complete container solution."
    
    elif 'eks' in text_lower or 'elastic kubernetes' in text_lower or 'kubernetes' in text_lower:
        return "Amazon EKS (Elastic Kubernetes Service) is a managed Kubernetes service that makes it easy to run Kubernetes on AWS without needing to install, operate, and maintain your own Kubernetes control plane. EKS automatically manages the availability and scalability of Kubernetes API servers and etcd persistence layer. It's certified Kubernetes conformant and integrates with AWS services like ELB, IAM, and VPC."
    
    elif 'fargate' in text_lower:
        return "AWS Fargate is a serverless compute engine for containers that works with both Amazon ECS and Amazon EKS. Fargate removes the need to provision and manage servers, letting you specify and pay for resources per application. It isolates applications by design and improves security. You simply package your application in containers, specify CPU and memory requirements, and Fargate handles the rest."
    
    elif 'elastic beanstalk' in text_lower or 'beanstalk' in text_lower:
        return "AWS Elastic Beanstalk is a Platform as a Service (PaaS) that makes it easy to deploy and scale web applications and services. Simply upload your code and Beanstalk automatically handles deployment, capacity provisioning, load balancing, auto-scaling, and application health monitoring. Supports Java, .NET, PHP, Node.js, Python, Ruby, Go, and Docker on familiar servers like Apache, Nginx, IIS."
    
    # Storage Services
    elif 's3' in text_lower or 'simple storage' in text_lower:
        return "Amazon S3 (Simple Storage Service) is object storage built to store and retrieve any amount of data from anywhere. It offers 99.999999999% (11 9's) durability and scales past trillions of objects. Storage classes include S3 Standard, S3 Intelligent-Tiering, S3 Standard-IA, S3 One Zone-IA, S3 Glacier, and S3 Glacier Deep Archive. Features include versioning, lifecycle policies, encryption, access control, and event notifications. Common uses: backups, data lakes, content distribution, archiving, disaster recovery."
    
    elif 'ebs' in text_lower or 'elastic block store' in text_lower:
        return "Amazon EBS (Elastic Block Store) provides persistent block storage volumes for use with EC2 instances. EBS volumes are automatically replicated within their Availability Zone for high availability and durability. Volume types include: General Purpose SSD (gp3, gp2), Provisioned IOPS SSD (io2, io1) for mission-critical applications, Throughput Optimized HDD (st1) for big data, and Cold HDD (sc1) for infrequent access. Supports snapshots for backups and encryption."
    
    elif 'efs' in text_lower or 'elastic file system' in text_lower:
        return "Amazon EFS (Elastic File System) provides a simple, serverless, elastic file system for use with AWS Cloud services and on-premises resources. It automatically grows and shrinks as you add and remove files, with no need for provisioning. EFS supports the Network File System (NFS) protocol and can be mounted on thousands of EC2 instances simultaneously. Perfect for content management, web serving, and data sharing workflows."
    
    elif 'fsx' in text_lower:
        return "Amazon FSx provides fully managed third-party file systems. FSx for Windows File Server offers fully managed Windows native shared storage with SMB protocol support, Active Directory integration, and Windows NTFS. FSx for Lustre provides high-performance file systems for compute-intensive workloads like machine learning, HPC, video processing, and financial modeling. Both offer high throughput, low latency, and integration with other AWS services."
    
    elif 'glacier' in text_lower:
        return "Amazon S3 Glacier and S3 Glacier Deep Archive are secure, durable, and extremely low-cost cloud storage classes for data archiving and long-term backup. Glacier provides three retrieval options: Expedited (1-5 minutes), Standard (3-5 hours), and Bulk (5-12 hours). Glacier Deep Archive is the lowest-cost storage in AWS, ideal for data that is accessed once or twice per year with retrieval times of 12 hours."
    
    # Database Services
    elif 'dynamodb' in text_lower or 'dynamo db' in text_lower:
        return "Amazon DynamoDB is a fully managed, serverless NoSQL database delivering single-digit millisecond performance at any scale. It offers built-in security, continuous backups, automated multi-Region replication, and in-memory caching with DAX. DynamoDB supports both key-value and document data structures. Features include Global Tables for multi-region deployment, DynamoDB Streams for change data capture, and on-demand or provisioned capacity modes. Perfect for mobile, web, gaming, ad tech, and IoT."
    
    elif 'rds' in text_lower or 'relational database service' in text_lower:
        return "Amazon RDS (Relational Database Service) makes it easy to set up, operate, and scale relational databases in the cloud. Supports six popular engines: Amazon Aurora, PostgreSQL, MySQL, MariaDB, Oracle, and SQL Server. RDS automates time-consuming tasks like hardware provisioning, database setup, patching, and backups. Features include Multi-AZ deployments for high availability, Read Replicas for read scaling, automated backups, and point-in-time recovery."
    
    elif 'aurora' in text_lower:
        return "Amazon Aurora is a MySQL and PostgreSQL-compatible relational database built for the cloud, combining performance and availability of commercial databases with the simplicity and cost-effectiveness of open source. Aurora is up to 5x faster than MySQL and 3x faster than PostgreSQL. It offers up to 15 low-latency read replicas, point-in-time recovery, continuous backup to S3, and replication across three Availability Zones. Aurora Serverless automatically scales capacity based on application needs."
    
    elif 'redshift' in text_lower:
        return "Amazon Redshift is a fast, fully managed cloud data warehouse that makes it simple and cost-effective to analyze data using SQL and existing BI tools. Redshift delivers 10x faster performance than other data warehouses by using machine learning, massively parallel query execution, and columnar storage. It can query exabytes of data in S3 using Redshift Spectrum. Features include automatic backups, snapshots, encryption, and integration with AWS analytics services."
    
    elif 'elasticache' in text_lower or 'elastic cache' in text_lower:
        return "Amazon ElastiCache is a fully managed in-memory data store and cache service supporting Redis and Memcached. It delivers sub-millisecond latency and is ideal for caching, session stores, gaming leaderboards, geospatial applications, and real-time analytics. ElastiCache for Redis supports data structures like strings, lists, sets, and sorted sets, plus features like replication, snapshots, and automatic failover. Memcached is great for simple caching use cases."
    
    elif 'neptune' in text_lower:
        return "Amazon Neptune is a fast, reliable, fully managed graph database service for applications that work with highly connected datasets. It supports both Property Graph (Apache TinkerPop Gremlin) and RDF (SPARQL) graph models. Neptune is optimized for storing billions of relationships and querying with milliseconds latency. Use cases include social networking, recommendation engines, fraud detection, knowledge graphs, and network/IT operations."
    
    elif 'documentdb' in text_lower or 'document db' in text_lower:
        return "Amazon DocumentDB is a fast, scalable, highly available, and fully managed document database service that supports MongoDB workloads. It's designed from the ground-up to give you the performance, scalability, and availability you need when operating mission-critical MongoDB workloads at scale. DocumentDB storage automatically scales up to 64 TB, supports millions of requests per second, and offers 6-way replication across three Availability Zones."
    
    # Networking & Content Delivery
    elif 'vpc' in text_lower or 'virtual private cloud' in text_lower:
        return "Amazon VPC (Virtual Private Cloud) lets you provision a logically isolated section of AWS Cloud where you launch resources in a virtual network you define. You control IP address ranges, subnets, route tables, network gateways, and security settings. Features include: multiple connectivity options (VPN, Direct Connect), security groups, network ACLs, VPC peering, VPC endpoints, NAT gateways, and internet gateways. VPC enables you to build secure, multi-tier web applications."
    
    elif 'cloudfront' in text_lower:
        return "Amazon CloudFront is a fast content delivery network (CDN) that securely delivers data, videos, applications, and APIs to customers globally with low latency and high transfer speeds. CloudFront has 400+ Points of Presence (edge locations) worldwide. It integrates with AWS Shield for DDoS protection, AWS WAF for web application firewall, and supports HTTPS. Perfect for streaming media, software downloads, and accelerating dynamic websites."
    
    elif 'route 53' in text_lower or 'route53' in text_lower or 'dns' in text_lower:
        return "Amazon Route 53 is a highly available and scalable Domain Name System (DNS) web service designed to route end users to applications. It offers three main functions: domain registration, DNS routing, and health checking. Route 53 supports various routing policies: simple, weighted, latency-based, failover, geolocation, and geoproximity. It integrates with other AWS services and provides 100% SLA for availability."
    
    elif 'direct connect' in text_lower:
        return "AWS Direct Connect creates a dedicated private network connection from your data center to AWS. This provides more consistent network performance, reduces bandwidth costs, and can be used as an alternative to internet-based connections. Direct Connect supports 1 Gbps and 10 Gbps connections and can be partitioned into multiple virtual interfaces. It's ideal for hybrid cloud architectures, large dataset transfers, and real-time data feeds."
    
    elif 'elb' in text_lower or 'elastic load balanc' in text_lower or 'load balanc' in text_lower:
        return "Elastic Load Balancing (ELB) automatically distributes incoming application traffic across multiple targets like EC2 instances, containers, and IP addresses. AWS offers four types: Application Load Balancer (Layer 7, HTTP/HTTPS), Network Load Balancer (Layer 4, extreme performance), Gateway Load Balancer (deploy/scale virtual appliances), and Classic Load Balancer (legacy). Features include health checks, SSL termination, sticky sessions, and integration with Auto Scaling."
    
    # Security, Identity & Compliance
    elif 'iam' in text_lower or ('identity' in text_lower and 'access' in text_lower):
        return "AWS IAM (Identity and Access Management) enables secure control of access to AWS services and resources. Create and manage users, groups, and roles with granular permissions. IAM supports: Multi-Factor Authentication (MFA), identity federation (SAML, OIDC), fine-grained access policies (JSON), temporary security credentials, and access keys for programmatic access. IAM follows the principle of least privilege and integrates with all AWS services. Best practices include using roles for applications and enabling MFA."
    
    elif 'cognito' in text_lower:
        return "Amazon Cognito provides authentication, authorization, and user management for web and mobile apps. It has two main components: User Pools (sign-up/sign-in functionality with user directory) and Identity Pools (grant users access to AWS services). Cognito supports social identity providers (Facebook, Google, Amazon), SAML, and custom authentication. Features include MFA, account recovery, advanced security features, and customizable UI. Scales to millions of users."
    
    elif 'kms' in text_lower or 'key management' in text_lower:
        return "AWS KMS (Key Management Service) makes it easy to create and control cryptographic keys used to encrypt data. KMS uses Hardware Security Modules (HSMs) to protect keys. It integrates with most AWS services (S3, EBS, RDS, etc.) for encryption at rest. Features include automatic key rotation, audit trails via CloudTrail, and support for symmetric and asymmetric keys. You can use AWS managed keys, customer managed keys, or import your own keys."
    
    elif 'secrets manager' in text_lower:
        return "AWS Secrets Manager helps you protect secrets needed to access applications, services, and IT resources. It enables you to easily rotate, manage, and retrieve database credentials, API keys, and other secrets throughout their lifecycle. Secrets Manager integrates with RDS, Redshift, and DocumentDB for automatic credential rotation. It provides fine-grained access control using IAM policies and encrypts secrets using KMS. Helps meet security and compliance requirements."
    
    elif 'waf' in text_lower or 'web application firewall' in text_lower:
        return "AWS WAF (Web Application Firewall) protects web applications from common web exploits and bots that could affect availability, compromise security, or consume excessive resources. Create custom rules to block attack patterns like SQL injection and cross-site scripting (XSS). WAF integrates with CloudFront, Application Load Balancer, API Gateway, and AppSync. Features include managed rule groups, rate limiting, IP reputation lists, and real-time metrics."
    
    elif 'shield' in text_lower:
        return "AWS Shield is a managed DDoS (Distributed Denial of Service) protection service. Shield Standard is automatically enabled for all AWS customers at no additional cost, protecting against common network and transport layer attacks. Shield Advanced provides enhanced protections, DDoS cost protection, 24/7 access to AWS DDoS Response Team (DRT), and real-time attack diagnostics. It integrates with CloudFront, Route 53, and Elastic Load Balancing."
    
    # Analytics
    elif 'athena' in text_lower:
        return "Amazon Athena is an interactive query service that makes it easy to analyze data in S3 using standard SQL. Athena is serverless, so there's no infrastructure to manage. You pay only for the queries you run. It can handle various data formats including CSV, JSON, ORC, Avro, and Parquet. Athena integrates with AWS Glue Data Catalog for metadata management. Perfect for ad-hoc queries, log analysis, and quick data exploration."
    
    elif 'emr' in text_lower or 'elastic mapreduce' in text_lower:
        return "Amazon EMR (Elastic MapReduce) is a cloud big data platform for processing vast amounts of data using open-source tools such as Apache Spark, Apache Hive, Apache HBase, Apache Flink, Apache Hudi, and Presto. EMR makes it easy to set up, operate, and scale your big data environments. Use cases include machine learning, log analysis, clickstream analysis, genomics, and financial analysis. EMR integrates with S3, DynamoDB, and other AWS services."
    
    elif 'kinesis' in text_lower:
        return "Amazon Kinesis makes it easy to collect, process, and analyze real-time streaming data. It has four services: Kinesis Data Streams (real-time data streaming), Kinesis Data Firehose (load streaming data into data lakes and analytics services), Kinesis Data Analytics (analyze streams using SQL or Apache Flink), and Kinesis Video Streams (video streaming). Use cases include log and event data collection, real-time analytics, IoT telemetry, and application monitoring."
    
    elif 'glue' in text_lower and 'aws' in text_lower:
        return "AWS Glue is a fully managed extract, transform, and load (ETL) service that makes it easy to prepare and load data for analytics. Glue automatically discovers and catalogs metadata about your data stores. It generates ETL code in Python or Scala to transform data. Features include: Glue Data Catalog (centralized metadata repository), Glue Crawlers (automatic schema discovery), job scheduling, and serverless execution. Perfect for data lake and data warehouse ETL workflows."
    
    elif 'quicksight' in text_lower:
        return "Amazon QuickSight is a fast, cloud-powered business intelligence (BI) service that makes it easy to deliver insights to everyone in your organization. QuickSight can automatically discover AWS data sources and connect to various databases. It uses SPICE (Super-fast, Parallel, In-memory Calculation Engine) for blazing-fast performance. Features include ML Insights, embedded analytics, mobile apps, and Pay-per-Session pricing. Create interactive dashboards and share insights easily."
    
    # Application Integration
    elif 'sns' in text_lower or 'simple notification' in text_lower:
        return "Amazon SNS (Simple Notification Service) is a fully managed pub/sub messaging service for both application-to-application (A2A) and application-to-person (A2P) communication. SNS enables you to send messages to large numbers of subscribers including distributed systems, mobile devices, and email addresses. It supports message filtering, delivery retries, DLQ (Dead Letter Queues), and message encryption. Use cases include application alerts, workflow systems, mobile push notifications, and SMS messaging."
    
    elif 'sqs' in text_lower or 'simple queue' in text_lower:
        return "Amazon SQS (Simple Queue Service) is a fully managed message queuing service that enables you to decouple and scale microservices, distributed systems, and serverless applications. SQS offers two queue types: Standard (unlimited throughput, best-effort ordering) and FIFO (exactly-once processing, preserved message order). Features include message retention up to 14 days, long polling, batch operations, server-side encryption, and DLQ for failed messages."
    
    elif 'eventbridge' in text_lower or 'event bridge' in text_lower:
        return "Amazon EventBridge is a serverless event bus service that makes it easy to connect applications using data from your own apps, SaaS applications, and AWS services. EventBridge delivers a stream of real-time data from sources like Salesforce, Zendesk, and Datadog, and routes that data to targets like Lambda, SNS, and Kinesis. Features include schema registry, content-based filtering, input transformation, and event replay. Perfect for building event-driven architectures."
    
    elif 'step functions' in text_lower:
        return "AWS Step Functions is a serverless orchestration service that lets you coordinate multiple AWS services into serverless workflows. You design workflows as state machines using Amazon States Language (JSON). Step Functions automatically triggers and tracks each step, retrying when there are errors. It integrates with Lambda, ECS, SNS, SQS, Glue, SageMaker, and more. Use cases include data processing pipelines, microservice orchestration, and IT automation."
    
    # Developer Tools
    elif 'codecommit' in text_lower or 'code commit' in text_lower:
        return "AWS CodeCommit is a fully managed source control service that hosts secure Git repositories. It eliminates the need to operate your own source control system and scales seamlessly. CodeCommit is integrated with IAM for access control and supports pull requests, branch policies, and code reviews. It integrates with other AWS developer tools and third-party tools. Your repositories are encrypted at rest and in transit."
    
    elif 'codebuild' in text_lower or 'code build' in text_lower:
        return "AWS CodeBuild is a fully managed continuous integration service that compiles source code, runs tests, and produces software packages ready to deploy. CodeBuild scales continuously and processes multiple builds concurrently. You pay only for the build time you use. It comes with pre-packaged build environments for popular programming languages, or you can create custom build environments using Docker images. Integrates with CodeCommit, GitHub, and other SCM tools."
    
    elif 'codedeploy' in text_lower or 'code deploy' in text_lower:
        return "AWS CodeDeploy is a fully managed deployment service that automates software deployments to various compute services such as EC2, Fargate, Lambda, and on-premises servers. CodeDeploy makes it easier to rapidly release new features, helps avoid downtime during deployment, and handles the complexity of updating applications. Supports blue/green deployments, rolling deployments, and canary deployments. Integrates with CI/CD pipelines and existing tools."
    
    elif 'codepipeline' in text_lower or 'code pipeline' in text_lower:
        return "AWS CodePipeline is a fully managed continuous delivery service that helps you automate your release pipelines for fast and reliable application updates. CodePipeline automates the build, test, and deploy phases of your release process every time there is a code change. It integrates with CodeCommit, CodeBuild, CodeDeploy, GitHub, Jenkins, and third-party services. You can create end-to-end CI/CD pipelines with custom workflows."
    
    elif 'cloud9' in text_lower:
        return "AWS Cloud9 is a cloud-based integrated development environment (IDE) that lets you write, run, and debug code with just a browser. It includes a code editor, debugger, and terminal. Cloud9 comes pre-packaged with essential tools for popular programming languages including JavaScript, Python, PHP, and more. It provides a seamless experience for developing serverless applications with direct access to AWS services and Lambda testing capabilities."
    
    # Management & Governance  
    elif 'cloudformation' in text_lower or 'cfn' in text_lower:
        return "AWS CloudFormation provides Infrastructure as Code (IaC) to model and provision all your cloud infrastructure resources. Describe your resources in YAML or JSON templates and CloudFormation handles the provisioning and configuration. It supports over 700 AWS resource types and enables you to treat infrastructure as code, version control your templates, and replicate environments consistently. Features include drift detection, change sets, stack policies, and StackSets for multi-account/region deployment."
    
    elif 'cloudtrail' in text_lower:
        return "AWS CloudTrail enables governance, compliance, operational auditing, and risk auditing of your AWS account. CloudTrail logs, continuously monitors, and retains account activity across your AWS infrastructure, giving you control over storage, analysis, and remediation actions. It records API calls made through AWS Management Console, SDKs, CLI, and other AWS services. CloudTrail Insights automatically analyzes write management events to detect unusual activity."
    
    elif 'cloudwatch' in text_lower:
        return "Amazon CloudWatch is a comprehensive monitoring and observability service for AWS resources and applications. It collects monitoring and operational data in the form of logs, metrics, and events. Features include: CloudWatch Metrics for monitoring, CloudWatch Logs for centralized log management, CloudWatch Alarms for automated actions, CloudWatch Dashboards for visualization, CloudWatch Events/EventBridge for event-driven automation, and CloudWatch Insights for log analytics. Supports custom metrics and application-level monitoring."
    
    elif 'systems manager' in text_lower or 'ssm' in text_lower:
        return "AWS Systems Manager gives you visibility and control of your infrastructure on AWS. It provides a unified user interface to view operational data from multiple AWS services and automate tasks across your resources. Key capabilities include: Parameter Store (secure configuration storage), Session Manager (browser-based shell access), Patch Manager (automated patching), Run Command (remote command execution), State Manager (configuration compliance), and OpsCenter (centralized operational data). Perfect for fleet management and automation."
    
    elif 'organizations' in text_lower:
        return "AWS Organizations helps you centrally manage and govern your environment as you grow and scale AWS resources. It enables you to create groups of accounts and apply policies to those groups. Features include: consolidated billing, Service Control Policies (SCPs) for access control, automated account creation, and resource sharing via AWS RAM. Organizations supports organizational units (OUs) for hierarchical grouping and makes it easier to manage security and compliance at scale."
    
    elif 'config' in text_lower and 'aws' in text_lower:
        return "AWS Config is a service that enables you to assess, audit, and evaluate the configurations of your AWS resources. Config continuously monitors and records AWS resource configurations and allows you to automate evaluation against desired configurations. It provides configuration snapshots and history, compliance checking, change tracking, and relationship tracking between resources. Use Config Rules for compliance checks and remediation actions to automatically fix non-compliant resources."
    
    elif 'trusted advisor' in text_lower:
        return "AWS Trusted Advisor is an online tool that provides real-time guidance to help you provision resources following AWS best practices. It inspects your AWS environment and makes recommendations across five categories: Cost Optimization, Performance, Security, Fault Tolerance, and Service Limits. Basic Support and Developer Support plans get access to 7 core checks. Business and Enterprise Support plans get full access to all checks plus automated actions and weekly updates."
    
    # AI & Machine Learning
    elif 'sagemaker' in text_lower or 'sage maker' in text_lower:
        return "Amazon SageMaker is a fully managed machine learning service that enables developers and data scientists to build, train, and deploy ML models quickly. SageMaker provides every component for machine learning in a single toolset. Features include: SageMaker Studio (IDE), built-in algorithms, AutoML, model training and tuning, one-click deployment, real-time and batch inference, model monitoring, and MLOps capabilities. It supports popular ML frameworks like TensorFlow, PyTorch, and scikit-learn."
    
    elif 'rekognition' in text_lower:
        return "Amazon Rekognition makes it easy to add image and video analysis to applications using deep learning technology. It can identify objects, people, text, scenes, and activities in images and videos, as well as detect inappropriate content. Rekognition also provides facial analysis and facial search capabilities. Use cases include content moderation, face-based user verification, sentiment analysis, celebrity recognition, and text detection in images."
    
    elif 'comprehend' in text_lower:
        return "Amazon Comprehend is a natural language processing (NLP) service that uses machine learning to find insights and relationships in text. It can identify the language of the text, extract key phrases, places, people, brands, or events, understand sentiment (positive, negative, neutral, mixed), analyze text using tokenization and parts of speech, and organize documents by topic. Comprehend can process documents in multiple languages and custom entity recognition."
    
    elif 'polly' in text_lower:
        return "Amazon Polly is a text-to-speech service that turns text into lifelike speech. Polly uses deep learning technologies to synthesize natural-sounding human speech in dozens of languages and various voices. It supports Speech Synthesis Markup Language (SSML) for pronunciation control, breathing sounds, whispering, and speech rate. Polly offers standard voices and Neural Text-to-Speech (NTTS) voices for more natural and human-like speech. Use cases include accessibility features, eLearning, and voice-enabled applications."
    
    elif 'transcribe' in text_lower:
        return "Amazon Transcribe is an automatic speech recognition (ASR) service that makes it easy to add speech-to-text capabilities to applications. Transcribe can handle poor audio quality, multiple speakers, and various audio formats. Features include: automatic punctuation, custom vocabulary, speaker identification, channel identification, content redaction (PII removal), language identification, and custom language models. Supports both batch and real-time transcription in multiple languages."
    
    elif 'translate' in text_lower and 'aws' in text_lower:
        return "Amazon Translate is a neural machine translation service that delivers fast, high-quality, and affordable language translation. It uses deep learning methods to provide more accurate and natural-sounding translations than traditional statistical and rule-based algorithms. Translate supports over 75 languages and can translate documents, websites, and applications. Features include custom terminology, parallel data for customization, and automatic language detection."
    
    elif 'lex' in text_lower or 'chatbot' in text_lower:
        return "Amazon Lex is a service for building conversational interfaces using voice and text. It provides advanced deep learning functionalities of automatic speech recognition (ASR) for converting speech to text, and natural language understanding (NLU) to recognize the intent of text. Lex powers Amazon Alexa and enables you to build sophisticated chatbots. Features include multi-turn conversations, context management, session attributes, Lambda integration, and deployment to multiple platforms (Facebook, Slack, Twilio)."
    
    elif 'bedrock' in text_lower:
        return "Amazon Bedrock is a fully managed service that offers a choice of high-performing foundation models (FMs) from leading AI companies including AI21 Labs, Anthropic, Cohere, Meta, Stability AI, and Amazon. With Bedrock you can experiment with and evaluate top FMs, customize them with your data using techniques like fine-tuning and RAG (Retrieval Augmented Generation), and build agents that execute tasks using your systems. Bedrock provides security, privacy, and responsible AI features built-in."
    
    # IoT
    elif 'iot core' in text_lower or 'iot' in text_lower:
        return "AWS IoT Core is a managed cloud service that lets connected devices easily and securely interact with cloud applications and other devices. IoT Core supports billions of devices and trillions of messages, processing and routing them to AWS endpoints and other devices reliably and securely. Features include device gateway, message broker, rules engine for data processing and integration, device shadow for device state management, and device defender for security. Supports MQTT, HTTPS, and WebSockets protocols."
    
    elif 'greengrass' in text_lower:
        return "AWS IoT Greengrass extends AWS to edge devices so they can act locally on the data they generate, while still using the cloud for management, analytics, and durable storage. With Greengrass, devices can run AWS Lambda functions, execute predictions based on machine learning models, keep device data in sync, and communicate with other devices securely, even without internet connectivity. It enables local data processing, ML inference, and messaging."
    
    # Migration & Transfer
    elif 'dms' in text_lower or 'database migration' in text_lower:
        return "AWS DMS (Database Migration Service) helps you migrate databases to AWS quickly and securely. The source database remains fully operational during migration, minimizing downtime. DMS supports homogeneous migrations (Oracle to Oracle) and heterogeneous migrations (Oracle to Aurora). It continuously replicates data with high availability and supports popular databases including Oracle, SQL Server, MySQL, PostgreSQL, MongoDB, and more. Features include Schema Conversion Tool (SCT) for converting database schemas."
    
    elif 'snowball' in text_lower or 'snow family' in text_lower:
        return "AWS Snow Family consists of physical devices to physically transport data into and out of AWS. Snowball Edge (80TB or 210TB) is a data migration and edge computing device. Snowcone (8TB) is the smallest device for edge computing and data transfer. Snowmobile is an exabyte-scale data transfer service (up to 100PB per Snowmobile). These devices are ideal for large-scale data transfers, disconnected environments, disaster recovery, and edge computing where bandwidth is limited or expensive."
    
    elif 'transfer family' in text_lower or 'sftp' in text_lower and 'aws' in text_lower:
        return "AWS Transfer Family provides fully managed support for file transfers directly into and out of Amazon S3 or Amazon EFS using SFTP, FTPS, and FTP protocols. Transfer Family handles the infrastructure, scaling, and availability. Features include integration with existing authentication systems (Active Directory, LDAP), custom identity providers, IP whitelisting, and CloudWatch logging. Perfect for migrating file transfer workloads to AWS while maintaining existing client integrations."
    
    # Others
    elif 'lightsail' in text_lower:
        return "Amazon Lightsail is designed to be the easiest way to launch and manage a virtual private server with AWS. Lightsail offers simple virtual private servers (VPS), containers, storage, databases, and networking at a cost-effective monthly price. It's ideal for simpler workloads, quick deployments, and getting started with AWS. Lightsail includes everything needed to jumpstart a project: virtual machine, SSD storage, data transfer, DNS management, and static IP."
    
    elif 'workspaces' in text_lower:
        return "Amazon WorkSpaces is a fully managed, secure Desktop-as-a-Service (DaaS) solution running on AWS. It allows you to provision cloud-based virtual desktops that allow end users to access documents, applications, and resources from any supported device including Windows and Mac computers, Chromebooks, iPads, and Android tablets. WorkSpaces offers flexible pricing, easy deployment and management, and integration with existing Active Directory."
    
    elif 'appstream' in text_lower or 'app stream' in text_lower:
        return "Amazon AppStream 2.0 is a fully managed application streaming service that provides users instant access to desktop applications from anywhere. It streams desktop applications from AWS to any device running a web browser, without rewriting applications. AppStream 2.0 handles scaling, manages and secures underlying infrastructure, and provides monitoring capabilities. Use cases include: application delivery to remote users, BYOD environments, and trial/demo applications."
    
    elif 'amplify' in text_lower:
        return "AWS Amplify is a complete solution for building full-stack web and mobile applications on AWS. It provides a development platform with libraries, UI components, and CLI for building apps faster. Amplify Console offers a Git-based workflow for hosting full-stack serverless web apps with continuous deployment. Features include authentication (Cognito), API (AppSync/API Gateway), storage (S3), analytics, ML predictions, and more. Supports React, Angular, Vue, iOS, Android, and Flutter."
    
    elif 'sam' in text_lower or 'serverless application model' in text_lower:
        return "AWS SAM (Serverless Application Model) is an open-source framework for building serverless applications on AWS. SAM extends CloudFormation with simplified syntax for defining Lambda functions, APIs (API Gateway), DynamoDB tables, and more. The SAM CLI provides local testing and debugging capabilities, allowing you to invoke functions locally, start a local API Gateway, and generate sample event payloads. SAM automates best practices for serverless development and deployment."
    
    else:
        return f"I can help you with information about 60+ AWS services including: Compute (Lambda, EC2, ECS, EKS, Fargate), Storage (S3, EBS, EFS, FSx), Database (DynamoDB, RDS, Aurora, Redshift), Networking (VPC, CloudFront, Route 53, ELB), Security (IAM, KMS, WAF, Shield), Analytics (Athena, EMR, Kinesis, QuickSight), AI/ML (SageMaker, Rekognition, Lex, Bedrock), Developer Tools (CodeCommit, CodeBuild, CodeDeploy), IoT (IoT Core, Greengrass), and more. You asked about '{text}' - could you please rephrase your question to mention a specific AWS service? For example: 'What is AWS Lambda?', 'Tell me about S3', or 'Explain ECS'."


def query_bedrock_kb(text):
    """
    Query Amazon Bedrock Knowledge Base with user input.
    
    Args:
        text (str): The user's input text to query
        
    Returns:
        str: The generated response from Bedrock Knowledge Base
    """
    # Check if Knowledge Base ID is configured
    if not KNOWLEDGE_BASE_ID:
        error_msg = "Knowledge Base ID is not configured."
        print(error_msg)
        return error_msg
    
    # Try multiple models in order of preference (using currently available models)
    models_to_try = [
        'anthropic.claude-3-5-sonnet-20240620-v1:0',   # Claude 3.5 Sonnet (2024 June release)
        'anthropic.claude-3-sonnet-20240229-v1:0',     # Claude 3 Sonnet
        'anthropic.claude-3-haiku-20240307-v1:0',      # Claude 3 Haiku (faster, cheaper fallback)
    ]
    
    last_error = None
    
    for model_id in models_to_try:
        try:
            # Construct the model ARN dynamically using the AWS region
            model_arn = f'arn:aws:bedrock:{AWS_REGION}::foundation-model/{model_id}'
            
            print(f"Querying Bedrock KB {KNOWLEDGE_BASE_ID} with text: {text}")
            print(f"Trying model ARN: {model_arn}")
            
            # Call Bedrock Knowledge Base retrieve_and_generate API
            response = bedrock_client.retrieve_and_generate(
                input={
                    'text': text
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                        'modelArn': model_arn
                    }
                }
            )
            
            # If successful, break out of the loop
            print(f"Successfully used model: {model_id}")
            break
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            last_error = e
            print(f"Model {model_id} failed with error: {error_code}")
            # Try next model
            continue
    else:
        # All models failed, use local knowledge base as fallback
        print(f"All Bedrock models failed. Using local knowledge base as fallback.")
        print(f"Last Bedrock error: {last_error}")
        return query_local_kb(text)
    
    try:
        
        # Extract the generated text from the response
        generated_text = response.get('output', {}).get('text', '')
        
        if not generated_text:
            print("Warning: Empty response from Bedrock Knowledge Base")
            return "I couldn't find relevant information in the knowledge base."
        
        print(f"Bedrock KB response: {generated_text}")
        return generated_text
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Bedrock ClientError [{error_code}]: {error_message}")
        
        # Provide user-friendly error messages
        if error_code == 'ResourceNotFoundException':
            return "The knowledge base could not be found. Please check the configuration."
        elif error_code == 'AccessDeniedException':
            return "I don't have permission to access the knowledge base."
        else:
            return "There was an error connecting to the knowledge base."
            
    except Exception as e:
        print(f"Unexpected error querying Bedrock KB: {str(e)}")
        return "There was an error connecting to the knowledge base."


def lambda_handler(event, context):
    """
    AWS Lambda handler for Amazon Lex V2 fulfillment hook.
    
    This function processes incoming Lex V2 events, handles various intents,
    and integrates with Amazon Bedrock Knowledge Base for fallback responses.
    
    Args:
        event (dict): Lex V2 event containing sessionId, intent, and user input
        context: Lambda context object
        
    Returns:
        dict: Lex V2 response format with session state and messages
    """
    try:
        # Log the incoming event for debugging
        print(f"Received Lex V2 event: {json.dumps(event)}")
        
        # Extract key information from the Lex V2 event
        session_id = event.get('sessionId', 'unknown-session')
        intent_name = event.get('sessionState', {}).get('intent', {}).get('name', 'Unknown')
        input_transcript = event.get('inputTranscript', '').strip()
        session_attributes = event.get('sessionState', {}).get('sessionAttributes', {})
        
        print(f"Processing - SessionID: {session_id}, Intent: {intent_name}, Input: {input_transcript}")
        
        # Load existing session data from DynamoDB
        session_data = get_session(session_id)
        
        # Initialize session data if it doesn't exist
        if not session_data:
            session_data = {
                'session_id': session_id,
                'conversation_history': [],
                'intent_count': {}
            }
        
        # Update conversation history
        if 'conversation_history' not in session_data:
            session_data['conversation_history'] = []
        
        # Intent-based response logic
        if intent_name == 'GreetingIntent':
            message = "Hello! How can I help you with your AWS questions?"
            
        elif intent_name == 'CheckStatusIntent':
            message = "I am checking your status now."
            
        else:
            # FallbackIntent or any other unrecognized intent
            if input_transcript:
                # Query Bedrock Knowledge Base with user input
                print(f"Fallback triggered - querying Bedrock KB with: {input_transcript}")
                message = query_bedrock_kb(input_transcript)
            else:
                # No input text available
                message = "I'm not sure how to help with that. Could you please rephrase your question?"
        
        # Track intent usage
        if 'intent_count' not in session_data:
            session_data['intent_count'] = {}
        
        session_data['intent_count'][intent_name] = session_data['intent_count'].get(intent_name, 0) + 1
        
        # Add current interaction to conversation history
        session_data['conversation_history'].append({
            'intent': intent_name,
            'user_input': input_transcript,
            'bot_response': message
        })
        
        # Limit conversation history to last 10 interactions
        if len(session_data['conversation_history']) > 10:
            session_data['conversation_history'] = session_data['conversation_history'][-10:]
        
        # Save updated session data to DynamoDB
        save_session(session_id, session_data)
        
        # Format and return Lex V2 response
        response = close(session_attributes, 'Fulfilled', message)
        
        print(f"Returning response: {json.dumps(response)}")
        return response
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        
        # Return error response to Lex
        error_response = close(
            session_attributes={},
            fulfillment_state='Failed',
            message_content="I apologize, but I encountered an error processing your request. Please try again."
        )
        
        return error_response

