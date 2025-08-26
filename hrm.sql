-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: hrm
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=169 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add budget category',7,'add_budgetcategory'),(26,'Can change budget category',7,'change_budgetcategory'),(27,'Can delete budget category',7,'delete_budgetcategory'),(28,'Can view budget category',7,'view_budgetcategory'),(29,'Can add client',8,'add_client'),(30,'Can change client',8,'change_client'),(31,'Can delete client',8,'delete_client'),(32,'Can view client',8,'view_client'),(33,'Can add department',9,'add_department'),(34,'Can change department',9,'change_department'),(35,'Can delete department',9,'delete_department'),(36,'Can view department',9,'view_department'),(37,'Can add designation',10,'add_designation'),(38,'Can change designation',10,'change_designation'),(39,'Can delete designation',10,'delete_designation'),(40,'Can view designation',10,'view_designation'),(41,'Can add budget',11,'add_budget'),(42,'Can change budget',11,'change_budget'),(43,'Can delete budget',11,'delete_budget'),(44,'Can view budget',11,'view_budget'),(45,'Can add budget expense',12,'add_budgetexpense'),(46,'Can change budget expense',12,'change_budgetexpense'),(47,'Can delete budget expense',12,'delete_budgetexpense'),(48,'Can view budget expense',12,'view_budgetexpense'),(49,'Can add budget revenue',13,'add_budgetrevenue'),(50,'Can change budget revenue',13,'change_budgetrevenue'),(51,'Can delete budget revenue',13,'delete_budgetrevenue'),(52,'Can view budget revenue',13,'view_budgetrevenue'),(53,'Can add chat message',14,'add_chatmessage'),(54,'Can change chat message',14,'change_chatmessage'),(55,'Can delete chat message',14,'delete_chatmessage'),(56,'Can view chat message',14,'view_chatmessage'),(57,'Can add employee',15,'add_employee'),(58,'Can change employee',15,'change_employee'),(59,'Can delete employee',15,'delete_employee'),(60,'Can view employee',15,'view_employee'),(61,'Can add holiday',16,'add_holiday'),(62,'Can change holiday',16,'change_holiday'),(63,'Can delete holiday',16,'delete_holiday'),(64,'Can view holiday',16,'view_holiday'),(65,'Can add leave',17,'add_leave'),(66,'Can change leave',17,'change_leave'),(67,'Can delete leave',17,'delete_leave'),(68,'Can view leave',17,'view_leave'),(69,'Can add online user',18,'add_onlineuser'),(70,'Can change online user',18,'change_onlineuser'),(71,'Can delete online user',18,'delete_onlineuser'),(72,'Can view online user',18,'view_onlineuser'),(73,'Can add payroll item',19,'add_payrollitem'),(74,'Can change payroll item',19,'change_payrollitem'),(75,'Can delete payroll item',19,'delete_payrollitem'),(76,'Can view payroll item',19,'view_payrollitem'),(77,'Can add payslip',20,'add_payslip'),(78,'Can change payslip',20,'change_payslip'),(79,'Can delete payslip',20,'delete_payslip'),(80,'Can view payslip',20,'view_payslip'),(81,'Can add project',21,'add_project'),(82,'Can change project',21,'change_project'),(83,'Can delete project',21,'delete_project'),(84,'Can view project',21,'view_project'),(85,'Can add task',22,'add_task'),(86,'Can change task',22,'change_task'),(87,'Can delete task',22,'delete_task'),(88,'Can view task',22,'view_task'),(89,'Can add ticket',23,'add_ticket'),(90,'Can change ticket',23,'change_ticket'),(91,'Can delete ticket',23,'delete_ticket'),(92,'Can view ticket',23,'view_ticket'),(93,'Can add attendance',24,'add_attendance'),(94,'Can change attendance',24,'change_attendance'),(95,'Can delete attendance',24,'delete_attendance'),(96,'Can view attendance',24,'view_attendance'),(97,'Can add asset',25,'add_asset'),(98,'Can change asset',25,'change_asset'),(99,'Can delete asset',25,'delete_asset'),(100,'Can view asset',25,'view_asset'),(101,'Can add company settings',26,'add_companysettings'),(102,'Can change company settings',26,'change_companysettings'),(103,'Can delete company settings',26,'delete_companysettings'),(104,'Can view company settings',26,'view_companysettings'),(105,'Can add localization settings',27,'add_localizationsettings'),(106,'Can change localization settings',27,'change_localizationsettings'),(107,'Can delete localization settings',27,'delete_localizationsettings'),(108,'Can view localization settings',27,'view_localizationsettings'),(109,'Can add invoice settings',28,'add_invoicesettings'),(110,'Can change invoice settings',28,'change_invoicesettings'),(111,'Can delete invoice settings',28,'delete_invoicesettings'),(112,'Can view invoice settings',28,'view_invoicesettings'),(113,'Can add salary settings',29,'add_salarysettings'),(114,'Can change salary settings',29,'change_salarysettings'),(115,'Can delete salary settings',29,'delete_salarysettings'),(116,'Can view salary settings',29,'view_salarysettings'),(117,'Can add theme settings',30,'add_themesettings'),(118,'Can change theme settings',30,'change_themesettings'),(119,'Can delete theme settings',30,'delete_themesettings'),(120,'Can view theme settings',30,'view_themesettings'),(121,'Can add tax',31,'add_tax'),(122,'Can change tax',31,'change_tax'),(123,'Can delete tax',31,'delete_tax'),(124,'Can view tax',31,'view_tax'),(125,'Can add expense',32,'add_expense'),(126,'Can change expense',32,'change_expense'),(127,'Can delete expense',32,'delete_expense'),(128,'Can view expense',32,'view_expense'),(129,'Can add estimate',33,'add_estimate'),(130,'Can change estimate',33,'change_estimate'),(131,'Can delete estimate',33,'delete_estimate'),(132,'Can view estimate',33,'view_estimate'),(133,'Can add estimate item',34,'add_estimateitem'),(134,'Can change estimate item',34,'change_estimateitem'),(135,'Can delete estimate item',34,'delete_estimateitem'),(136,'Can view estimate item',34,'view_estimateitem'),(137,'Can add invoice',35,'add_invoice'),(138,'Can change invoice',35,'change_invoice'),(139,'Can delete invoice',35,'delete_invoice'),(140,'Can view invoice',35,'view_invoice'),(141,'Can add invoice item',36,'add_invoiceitem'),(142,'Can change invoice item',36,'change_invoiceitem'),(143,'Can delete invoice item',36,'delete_invoiceitem'),(144,'Can view invoice item',36,'view_invoiceitem'),(145,'Can add attendance machine',37,'add_attendancemachine'),(146,'Can change attendance machine',37,'change_attendancemachine'),(147,'Can delete attendance machine',37,'delete_attendancemachine'),(148,'Can view attendance machine',37,'view_attendancemachine'),(149,'Can add attendance log',38,'add_attendancelog'),(150,'Can change attendance log',38,'change_attendancelog'),(151,'Can delete attendance log',38,'delete_attendancelog'),(152,'Can view attendance log',38,'view_attendancelog'),(153,'Can add tax slab',39,'add_taxslab'),(154,'Can change tax slab',39,'change_taxslab'),(155,'Can delete tax slab',39,'delete_taxslab'),(156,'Can view tax slab',39,'view_taxslab'),(157,'Can add loan',40,'add_loan'),(158,'Can change loan',40,'change_loan'),(159,'Can delete loan',40,'delete_loan'),(160,'Can view loan',40,'view_loan'),(161,'Can add monthly payroll run',41,'add_monthlypayrollrun'),(162,'Can change monthly payroll run',41,'change_monthlypayrollrun'),(163,'Can delete monthly payroll run',41,'delete_monthlypayrollrun'),(164,'Can view monthly payroll run',41,'view_monthlypayrollrun'),(165,'Can add advance request',42,'add_advancerequest'),(166,'Can change advance request',42,'change_advancerequest'),(167,'Can delete advance request',42,'delete_advancerequest'),(168,'Can view advance request',42,'view_advancerequest');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1000000$CDOra4DGmpOn4JkK6bGoVK$nAGTNFZF7XmAnkQgsGlgsn0ZYyNKS+6KlTOXuqdJ5Pk=','2025-08-22 14:13:54.224424',1,'admin','','','admin@example.com',1,1,'2025-08-22 14:12:34.555496');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_advancerequest`
--

DROP TABLE IF EXISTS `core_advancerequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_advancerequest` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(12,2) NOT NULL,
  `reason` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `desired_installments` int unsigned DEFAULT NULL,
  `status` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `requested_at` datetime(6) NOT NULL,
  `reviewed_at` datetime(6) DEFAULT NULL,
  `admin_comment` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `employee_id` bigint NOT NULL,
  `reviewed_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_advancerequest_employee_id_fa0a36d4_fk_core_employee_id` (`employee_id`),
  KEY `core_advancerequest_reviewed_by_id_4d8b7871_fk_auth_user_id` (`reviewed_by_id`),
  CONSTRAINT `core_advancerequest_employee_id_fa0a36d4_fk_core_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `core_employee` (`id`),
  CONSTRAINT `core_advancerequest_reviewed_by_id_4d8b7871_fk_auth_user_id` FOREIGN KEY (`reviewed_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_advancerequest_chk_1` CHECK ((`desired_installments` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_advancerequest`
--

LOCK TABLES `core_advancerequest` WRITE;
/*!40000 ALTER TABLE `core_advancerequest` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_advancerequest` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_asset`
--

DROP TABLE IF EXISTS `core_asset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_asset` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `asset_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_id` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `purchase_date` date DEFAULT NULL,
  `purchase_from` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `manufacturer` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `serial_number` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `brand` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `supplier` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `condition` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `warranty` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `warranty_end` date DEFAULT NULL,
  `cost` decimal(12,2) DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `files` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `asset_user_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `asset_id` (`asset_id`),
  KEY `core_asset_asset_user_id_73ee7e1a_fk_core_employee_id` (`asset_user_id`),
  CONSTRAINT `core_asset_asset_user_id_73ee7e1a_fk_core_employee_id` FOREIGN KEY (`asset_user_id`) REFERENCES `core_employee` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_asset`
--

LOCK TABLES `core_asset` WRITE;
/*!40000 ALTER TABLE `core_asset` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_asset` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_attendance`
--

DROP TABLE IF EXISTS `core_attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_attendance` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `check_in` datetime(6) DEFAULT NULL,
  `check_out` datetime(6) DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `employee_id` bigint NOT NULL,
  `break_start` datetime(6) DEFAULT NULL,
  `break_end` datetime(6) DEFAULT NULL,
  `total_work_hours` decimal(5,2) DEFAULT NULL,
  `total_break_hours` decimal(5,2) DEFAULT NULL,
  `is_late` tinyint(1) NOT NULL,
  `late_minutes` int NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `core_attendance_user_id_date_399e5e24_uniq` (`employee_id`,`date`),
  CONSTRAINT `core_attendance_employee_id_6327f987_fk_core_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `core_employee` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_attendance`
--

LOCK TABLES `core_attendance` WRITE;
/*!40000 ALTER TABLE `core_attendance` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_attendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_attendancelog`
--

DROP TABLE IF EXISTS `core_attendancelog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_attendancelog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `attendance_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `machine_timestamp` datetime(6) DEFAULT NULL,
  `machine_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `employee_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_attend_employe_584fa1_idx` (`employee_id`,`timestamp`),
  KEY `core_attend_timesta_22ab97_idx` (`timestamp`),
  CONSTRAINT `core_attendancelog_employee_id_77fa9230_fk_core_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `core_employee` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_attendancelog`
--

LOCK TABLES `core_attendancelog` WRITE;
/*!40000 ALTER TABLE `core_attendancelog` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_attendancelog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_attendancemachine`
--

DROP TABLE IF EXISTS `core_attendancemachine`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_attendancemachine` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip_address` char(39) COLLATE utf8mb4_unicode_ci NOT NULL,
  `port` int NOT NULL,
  `location` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `last_sync` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_attendancemachine`
--

LOCK TABLES `core_attendancemachine` WRITE;
/*!40000 ALTER TABLE `core_attendancemachine` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_attendancemachine` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_budget`
--

DROP TABLE IF EXISTS `core_budget`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_budget` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tax` decimal(12,2) NOT NULL,
  `period_start` date NOT NULL,
  `period_end` date NOT NULL,
  `attachment` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `note` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `category_id` bigint DEFAULT NULL,
  `project_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_budget_project_id_0de65dd3_fk_core_project_id` (`project_id`),
  KEY `core_budget_category_id_779c79ff_fk_core_budgetcategory_id` (`category_id`),
  CONSTRAINT `core_budget_category_id_779c79ff_fk_core_budgetcategory_id` FOREIGN KEY (`category_id`) REFERENCES `core_budgetcategory` (`id`),
  CONSTRAINT `core_budget_project_id_0de65dd3_fk_core_project_id` FOREIGN KEY (`project_id`) REFERENCES `core_project` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_budget`
--

LOCK TABLES `core_budget` WRITE;
/*!40000 ALTER TABLE `core_budget` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_budget` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_budgetcategory`
--

DROP TABLE IF EXISTS `core_budgetcategory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_budgetcategory` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_budgetcategory`
--

LOCK TABLES `core_budgetcategory` WRITE;
/*!40000 ALTER TABLE `core_budgetcategory` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_budgetcategory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_budgetexpense`
--

DROP TABLE IF EXISTS `core_budgetexpense`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_budgetexpense` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `date` date NOT NULL,
  `budget_id` bigint NOT NULL,
  `attachment` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_budgetexpense_budget_id_761ee208_fk_core_budget_id` (`budget_id`),
  CONSTRAINT `core_budgetexpense_budget_id_761ee208_fk_core_budget_id` FOREIGN KEY (`budget_id`) REFERENCES `core_budget` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_budgetexpense`
--

LOCK TABLES `core_budgetexpense` WRITE;
/*!40000 ALTER TABLE `core_budgetexpense` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_budgetexpense` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_budgetrevenue`
--

DROP TABLE IF EXISTS `core_budgetrevenue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_budgetrevenue` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `date` date NOT NULL,
  `budget_id` bigint NOT NULL,
  `attachment` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_budgetrevenue_budget_id_e968ab23_fk_core_budget_id` (`budget_id`),
  CONSTRAINT `core_budgetrevenue_budget_id_e968ab23_fk_core_budget_id` FOREIGN KEY (`budget_id`) REFERENCES `core_budget` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_budgetrevenue`
--

LOCK TABLES `core_budgetrevenue` WRITE;
/*!40000 ALTER TABLE `core_budgetrevenue` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_budgetrevenue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_chatmessage`
--

DROP TABLE IF EXISTS `core_chatmessage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_chatmessage` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `content` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `recipient_id` int NOT NULL,
  `sender_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_chatmessage_recipient_id_99e45b75_fk_auth_user_id` (`recipient_id`),
  KEY `core_chatmessage_sender_id_c9992722_fk_auth_user_id` (`sender_id`),
  CONSTRAINT `core_chatmessage_recipient_id_99e45b75_fk_auth_user_id` FOREIGN KEY (`recipient_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_chatmessage_sender_id_c9992722_fk_auth_user_id` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_chatmessage`
--

LOCK TABLES `core_chatmessage` WRITE;
/*!40000 ALTER TABLE `core_chatmessage` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_chatmessage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_client`
--

DROP TABLE IF EXISTS `core_client`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_client` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` longtext COLLATE utf8mb4_unicode_ci,
  `company` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_client`
--

LOCK TABLES `core_client` WRITE;
/*!40000 ALTER TABLE `core_client` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_client` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_companysettings`
--

DROP TABLE IF EXISTS `core_companysettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_companysettings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `company_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `contact_person` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `address` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `country` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `city` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `state_province` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `postal_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone_number` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `mobile_number` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fax` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `website_url` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_companysettings`
--

LOCK TABLES `core_companysettings` WRITE;
/*!40000 ALTER TABLE `core_companysettings` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_companysettings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_department`
--

DROP TABLE IF EXISTS `core_department`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_department` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_department`
--

LOCK TABLES `core_department` WRITE;
/*!40000 ALTER TABLE `core_department` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_department` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_designation`
--

DROP TABLE IF EXISTS `core_designation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_designation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_designation`
--

LOCK TABLES `core_designation` WRITE;
/*!40000 ALTER TABLE `core_designation` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_designation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_employee`
--

DROP TABLE IF EXISTS `core_employee`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_employee` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `salary` decimal(10,2) DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `address` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `date_of_joining` date DEFAULT NULL,
  `department_id` bigint DEFAULT NULL,
  `designation_id` bigint DEFAULT NULL,
  `user_id` int NOT NULL,
  `can_view_attendance` tinyint(1) NOT NULL,
  `can_view_department` tinyint(1) NOT NULL,
  `can_view_designation` tinyint(1) NOT NULL,
  `can_view_holidays` tinyint(1) NOT NULL,
  `can_view_leaves` tinyint(1) NOT NULL,
  `can_view_tasks` tinyint(1) NOT NULL,
  `is_restricted` tinyint(1) NOT NULL,
  `machine_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fingerprint_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `face_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `card_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_pay_date` date DEFAULT NULL,
  `pay_frequency` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `core_employee_department_id_ada9945f_fk_core_department_id` (`department_id`),
  KEY `core_employee_designation_id_4a999f3b_fk_core_designation_id` (`designation_id`),
  CONSTRAINT `core_employee_department_id_ada9945f_fk_core_department_id` FOREIGN KEY (`department_id`) REFERENCES `core_department` (`id`),
  CONSTRAINT `core_employee_designation_id_4a999f3b_fk_core_designation_id` FOREIGN KEY (`designation_id`) REFERENCES `core_designation` (`id`),
  CONSTRAINT `core_employee_user_id_938b4b84_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_employee`
--

LOCK TABLES `core_employee` WRITE;
/*!40000 ALTER TABLE `core_employee` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_employee` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_estimate`
--

DROP TABLE IF EXISTS `core_estimate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_estimate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `client_address` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `billing_address` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `estimate_date` date NOT NULL,
  `expiry_date` date NOT NULL,
  `discount` decimal(5,2) NOT NULL,
  `other_info` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `client_id` bigint NOT NULL,
  `project_id` bigint DEFAULT NULL,
  `tax_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_estimate_client_id_6536b5d6_fk_core_client_id` (`client_id`),
  KEY `core_estimate_project_id_b9a2ff1d_fk_core_project_id` (`project_id`),
  KEY `core_estimate_tax_id_111d3bf1_fk_core_tax_id` (`tax_id`),
  CONSTRAINT `core_estimate_client_id_6536b5d6_fk_core_client_id` FOREIGN KEY (`client_id`) REFERENCES `core_client` (`id`),
  CONSTRAINT `core_estimate_project_id_b9a2ff1d_fk_core_project_id` FOREIGN KEY (`project_id`) REFERENCES `core_project` (`id`),
  CONSTRAINT `core_estimate_tax_id_111d3bf1_fk_core_tax_id` FOREIGN KEY (`tax_id`) REFERENCES `core_tax` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_estimate`
--

LOCK TABLES `core_estimate` WRITE;
/*!40000 ALTER TABLE `core_estimate` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_estimate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_estimateitem`
--

DROP TABLE IF EXISTS `core_estimateitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_estimateitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(300) COLLATE utf8mb4_unicode_ci NOT NULL,
  `unit_cost` decimal(10,2) NOT NULL,
  `quantity` int unsigned NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `estimate_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_estimateitem_estimate_id_f6eff068_fk_core_estimate_id` (`estimate_id`),
  CONSTRAINT `core_estimateitem_estimate_id_f6eff068_fk_core_estimate_id` FOREIGN KEY (`estimate_id`) REFERENCES `core_estimate` (`id`),
  CONSTRAINT `core_estimateitem_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_estimateitem`
--

LOCK TABLES `core_estimateitem` WRITE;
/*!40000 ALTER TABLE `core_estimateitem` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_estimateitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_expense`
--

DROP TABLE IF EXISTS `core_expense`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_expense` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `purchased_from` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `purchased_date` date NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `paid_by` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_expense`
--

LOCK TABLES `core_expense` WRITE;
/*!40000 ALTER TABLE `core_expense` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_expense` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_holiday`
--

DROP TABLE IF EXISTS `core_holiday`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_holiday` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date` date NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_holiday_created_by_id_c60dda4b_fk_auth_user_id` (`created_by_id`),
  CONSTRAINT `core_holiday_created_by_id_c60dda4b_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_holiday`
--

LOCK TABLES `core_holiday` WRITE;
/*!40000 ALTER TABLE `core_holiday` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_holiday` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_invoice`
--

DROP TABLE IF EXISTS `core_invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_invoice` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `client_address` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `billing_address` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `invoice_date` date NOT NULL,
  `due_date` date NOT NULL,
  `discount` decimal(5,2) NOT NULL,
  `other_info` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `client_id` bigint NOT NULL,
  `project_id` bigint DEFAULT NULL,
  `tax_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_invoice_client_id_5b95bdaf_fk_core_client_id` (`client_id`),
  KEY `core_invoice_project_id_2f8fbf0f_fk_core_project_id` (`project_id`),
  KEY `core_invoice_tax_id_990f3a7e_fk_core_tax_id` (`tax_id`),
  CONSTRAINT `core_invoice_client_id_5b95bdaf_fk_core_client_id` FOREIGN KEY (`client_id`) REFERENCES `core_client` (`id`),
  CONSTRAINT `core_invoice_project_id_2f8fbf0f_fk_core_project_id` FOREIGN KEY (`project_id`) REFERENCES `core_project` (`id`),
  CONSTRAINT `core_invoice_tax_id_990f3a7e_fk_core_tax_id` FOREIGN KEY (`tax_id`) REFERENCES `core_tax` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_invoice`
--

LOCK TABLES `core_invoice` WRITE;
/*!40000 ALTER TABLE `core_invoice` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_invoice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_invoiceitem`
--

DROP TABLE IF EXISTS `core_invoiceitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_invoiceitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(300) COLLATE utf8mb4_unicode_ci NOT NULL,
  `unit_cost` decimal(10,2) NOT NULL,
  `quantity` int unsigned NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `invoice_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_invoiceitem_invoice_id_ed095f3b_fk_core_invoice_id` (`invoice_id`),
  CONSTRAINT `core_invoiceitem_invoice_id_ed095f3b_fk_core_invoice_id` FOREIGN KEY (`invoice_id`) REFERENCES `core_invoice` (`id`),
  CONSTRAINT `core_invoiceitem_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_invoiceitem`
--

LOCK TABLES `core_invoiceitem` WRITE;
/*!40000 ALTER TABLE `core_invoiceitem` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_invoiceitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_invoicesettings`
--

DROP TABLE IF EXISTS `core_invoicesettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_invoicesettings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `prefix` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `logo` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_invoicesettings`
--

LOCK TABLES `core_invoicesettings` WRITE;
/*!40000 ALTER TABLE `core_invoicesettings` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_invoicesettings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_leave`
--

DROP TABLE IF EXISTS `core_leave`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_leave` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `leave_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reason` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied_at` datetime(6) NOT NULL,
  `reviewed_at` datetime(6) DEFAULT NULL,
  `comments` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `employee_id` bigint NOT NULL,
  `reviewed_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_leave_employee_id_70e37b16_fk_core_employee_id` (`employee_id`),
  KEY `core_leave_reviewed_by_id_28f141f0_fk_auth_user_id` (`reviewed_by_id`),
  CONSTRAINT `core_leave_employee_id_70e37b16_fk_core_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `core_employee` (`id`),
  CONSTRAINT `core_leave_reviewed_by_id_28f141f0_fk_auth_user_id` FOREIGN KEY (`reviewed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_leave`
--

LOCK TABLES `core_leave` WRITE;
/*!40000 ALTER TABLE `core_leave` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_leave` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_loan`
--

DROP TABLE IF EXISTS `core_loan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_loan` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `principal_amount` decimal(12,2) NOT NULL,
  `monthly_installment` decimal(12,2) NOT NULL,
  `balance` decimal(12,2) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `employee_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_loan_employee_id_253ded63_fk_core_employee_id` (`employee_id`),
  CONSTRAINT `core_loan_employee_id_253ded63_fk_core_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `core_employee` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_loan`
--

LOCK TABLES `core_loan` WRITE;
/*!40000 ALTER TABLE `core_loan` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_loan` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_localizationsettings`
--

DROP TABLE IF EXISTS `core_localizationsettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_localizationsettings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `default_language` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `timezone` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date_format` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `time_format` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `currency` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `currency_symbol` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL,
  `thousand_separator` varchar(2) COLLATE utf8mb4_unicode_ci NOT NULL,
  `decimal_separator` varchar(2) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_localizationsettings`
--

LOCK TABLES `core_localizationsettings` WRITE;
/*!40000 ALTER TABLE `core_localizationsettings` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_localizationsettings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_monthlypayrollrun`
--

DROP TABLE IF EXISTS `core_monthlypayrollrun`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_monthlypayrollrun` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `period_start` date NOT NULL,
  `period_end` date NOT NULL,
  `run_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `period_start` (`period_start`),
  UNIQUE KEY `period_end` (`period_end`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_monthlypayrollrun`
--

LOCK TABLES `core_monthlypayrollrun` WRITE;
/*!40000 ALTER TABLE `core_monthlypayrollrun` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_monthlypayrollrun` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_onlineuser`
--

DROP TABLE IF EXISTS `core_onlineuser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_onlineuser` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `last_seen` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `core_onlineuser_user_id_7a06401c_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_onlineuser`
--

LOCK TABLES `core_onlineuser` WRITE;
/*!40000 ALTER TABLE `core_onlineuser` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_onlineuser` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_payrollitem`
--

DROP TABLE IF EXISTS `core_payrollitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_payrollitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_type` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `employee_id` bigint NOT NULL,
  `category` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `end_date` date DEFAULT NULL,
  `is_recurring` tinyint(1) NOT NULL,
  `start_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_payrollitem_employee_id_79ccd81c_fk_core_employee_id` (`employee_id`),
  CONSTRAINT `core_payrollitem_employee_id_79ccd81c_fk_core_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `core_employee` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_payrollitem`
--

LOCK TABLES `core_payrollitem` WRITE;
/*!40000 ALTER TABLE `core_payrollitem` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_payrollitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_payslip`
--

DROP TABLE IF EXISTS `core_payslip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_payslip` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `employee_id` bigint NOT NULL,
  `gross_pay` decimal(10,2) NOT NULL,
  `pdf` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `period_end` date DEFAULT NULL,
  `period_start` date DEFAULT NULL,
  `status` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `total_deductions` decimal(10,2) NOT NULL,
  `total_earnings` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_payslip_created_by_id_6404fb77_fk_auth_user_id` (`created_by_id`),
  KEY `core_payslip_employee_id_1c6556f2_fk_core_employee_id` (`employee_id`),
  CONSTRAINT `core_payslip_created_by_id_6404fb77_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_payslip_employee_id_1c6556f2_fk_core_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `core_employee` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_payslip`
--

LOCK TABLES `core_payslip` WRITE;
/*!40000 ALTER TABLE `core_payslip` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_payslip` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_project`
--

DROP TABLE IF EXISTS `core_project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_project` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `client_id` bigint NOT NULL,
  `manager_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_project_client_id_4ba9e455_fk_core_client_id` (`client_id`),
  KEY `core_project_manager_id_64f15e4b_fk_core_employee_id` (`manager_id`),
  CONSTRAINT `core_project_client_id_4ba9e455_fk_core_client_id` FOREIGN KEY (`client_id`) REFERENCES `core_client` (`id`),
  CONSTRAINT `core_project_manager_id_64f15e4b_fk_core_employee_id` FOREIGN KEY (`manager_id`) REFERENCES `core_employee` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_project`
--

LOCK TABLES `core_project` WRITE;
/*!40000 ALTER TABLE `core_project` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_project` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_salarysettings`
--

DROP TABLE IF EXISTS `core_salarysettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_salarysettings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `da_enabled` tinyint(1) NOT NULL,
  `da_percent` decimal(5,2) NOT NULL,
  `hra_enabled` tinyint(1) NOT NULL,
  `hra_percent` decimal(5,2) NOT NULL,
  `pf_enabled` tinyint(1) NOT NULL,
  `pf_employee_share` decimal(5,2) NOT NULL,
  `pf_org_share` decimal(5,2) NOT NULL,
  `esi_enabled` tinyint(1) NOT NULL,
  `esi_employee_share` decimal(5,2) NOT NULL,
  `esi_org_share` decimal(5,2) NOT NULL,
  `gratuity_enabled` tinyint(1) NOT NULL,
  `gratuity_employee_share` decimal(5,2) NOT NULL,
  `gratuity_org_share` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_salarysettings`
--

LOCK TABLES `core_salarysettings` WRITE;
/*!40000 ALTER TABLE `core_salarysettings` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_salarysettings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_task`
--

DROP TABLE IF EXISTS `core_task`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_task` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `deadline` date DEFAULT NULL,
  `priority` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `attachment` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `comment` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `assigned_by_id` bigint NOT NULL,
  `assigned_to_id` bigint NOT NULL,
  `project_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_task_assigned_by_id_4e83df82_fk_core_employee_id` (`assigned_by_id`),
  KEY `core_task_assigned_to_id_4a4e0391_fk_core_employee_id` (`assigned_to_id`),
  KEY `core_task_project_id_877ce78a_fk_core_project_id` (`project_id`),
  CONSTRAINT `core_task_assigned_by_id_4e83df82_fk_core_employee_id` FOREIGN KEY (`assigned_by_id`) REFERENCES `core_employee` (`id`),
  CONSTRAINT `core_task_assigned_to_id_4a4e0391_fk_core_employee_id` FOREIGN KEY (`assigned_to_id`) REFERENCES `core_employee` (`id`),
  CONSTRAINT `core_task_project_id_877ce78a_fk_core_project_id` FOREIGN KEY (`project_id`) REFERENCES `core_project` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_task`
--

LOCK TABLES `core_task` WRITE;
/*!40000 ALTER TABLE `core_task` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_task` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_tax`
--

DROP TABLE IF EXISTS `core_tax`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_tax` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `percentage` decimal(5,2) NOT NULL,
  `active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_tax`
--

LOCK TABLES `core_tax` WRITE;
/*!40000 ALTER TABLE `core_tax` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_tax` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_taxslab`
--

DROP TABLE IF EXISTS `core_taxslab`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_taxslab` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `min_income` decimal(12,2) NOT NULL,
  `max_income` decimal(12,2) DEFAULT NULL,
  `rate_percent` decimal(5,2) NOT NULL,
  `fixed_deduction` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_taxslab`
--

LOCK TABLES `core_taxslab` WRITE;
/*!40000 ALTER TABLE `core_taxslab` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_taxslab` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_themesettings`
--

DROP TABLE IF EXISTS `core_themesettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_themesettings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `logo_light` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `logo_dark` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `favicon` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `layout` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `layout_width` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `color_scheme` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `layout_position` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `topbar_color` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sidebar_size` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sidebar_view` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sidebar_color` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_themesettings`
--

LOCK TABLES `core_themesettings` WRITE;
/*!40000 ALTER TABLE `core_themesettings` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_themesettings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_ticket`
--

DROP TABLE IF EXISTS `core_ticket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_ticket` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `assigned_to_id` int DEFAULT NULL,
  `created_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_ticket_assigned_to_id_e0f94da4_fk_auth_user_id` (`assigned_to_id`),
  KEY `core_ticket_created_by_id_54de7906_fk_auth_user_id` (`created_by_id`),
  CONSTRAINT `core_ticket_assigned_to_id_e0f94da4_fk_auth_user_id` FOREIGN KEY (`assigned_to_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_ticket_created_by_id_54de7906_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_ticket`
--

LOCK TABLES `core_ticket` WRITE;
/*!40000 ALTER TABLE `core_ticket` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_ticket` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(42,'core','advancerequest'),(25,'core','asset'),(24,'core','attendance'),(38,'core','attendancelog'),(37,'core','attendancemachine'),(11,'core','budget'),(7,'core','budgetcategory'),(12,'core','budgetexpense'),(13,'core','budgetrevenue'),(14,'core','chatmessage'),(8,'core','client'),(26,'core','companysettings'),(9,'core','department'),(10,'core','designation'),(15,'core','employee'),(33,'core','estimate'),(34,'core','estimateitem'),(32,'core','expense'),(16,'core','holiday'),(35,'core','invoice'),(36,'core','invoiceitem'),(28,'core','invoicesettings'),(17,'core','leave'),(40,'core','loan'),(27,'core','localizationsettings'),(41,'core','monthlypayrollrun'),(18,'core','onlineuser'),(19,'core','payrollitem'),(20,'core','payslip'),(21,'core','project'),(29,'core','salarysettings'),(22,'core','task'),(31,'core','tax'),(39,'core','taxslab'),(30,'core','themesettings'),(23,'core','ticket'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2025-08-22 14:11:56.086043'),(2,'auth','0001_initial','2025-08-22 14:11:57.236119'),(3,'admin','0001_initial','2025-08-22 14:11:57.558783'),(4,'admin','0002_logentry_remove_auto_add','2025-08-22 14:11:57.586558'),(5,'admin','0003_logentry_add_action_flag_choices','2025-08-22 14:11:57.607730'),(6,'contenttypes','0002_remove_content_type_name','2025-08-22 14:11:57.923395'),(7,'auth','0002_alter_permission_name_max_length','2025-08-22 14:11:58.042064'),(8,'auth','0003_alter_user_email_max_length','2025-08-22 14:11:58.084783'),(9,'auth','0004_alter_user_username_opts','2025-08-22 14:11:58.105931'),(10,'auth','0005_alter_user_last_login_null','2025-08-22 14:11:58.240750'),(11,'auth','0006_require_contenttypes_0002','2025-08-22 14:11:58.250977'),(12,'auth','0007_alter_validators_add_error_messages','2025-08-22 14:11:58.285587'),(13,'auth','0008_alter_user_username_max_length','2025-08-22 14:11:58.443096'),(14,'auth','0009_alter_user_last_name_max_length','2025-08-22 14:11:58.558073'),(15,'auth','0010_alter_group_name_max_length','2025-08-22 14:11:58.592301'),(16,'auth','0011_update_proxy_permissions','2025-08-22 14:11:58.612934'),(17,'auth','0012_alter_user_first_name_max_length','2025-08-22 14:11:58.724207'),(18,'core','0001_initial','2025-08-22 14:12:01.932931'),(19,'core','0002_budgetexpense_attachment_budgetexpense_end_date_and_more','2025-08-22 14:12:02.203644'),(20,'core','0003_budgetrevenue_attachment_budgetrevenue_end_date_and_more','2025-08-22 14:12:02.500618'),(21,'core','0004_asset','2025-08-22 14:12:02.704111'),(22,'core','0005_companysettings','2025-08-22 14:12:02.740306'),(23,'core','0006_localizationsettings','2025-08-22 14:12:02.779866'),(24,'core','0007_invoicesettings','2025-08-22 14:12:02.810184'),(25,'core','0008_salarysettings','2025-08-22 14:12:02.853365'),(26,'core','0009_themesettings','2025-08-22 14:12:02.891219'),(27,'core','0010_tax','2025-08-22 14:12:02.927148'),(28,'core','0011_expense','2025-08-22 14:12:02.965820'),(29,'core','0012_estimate_estimateitem','2025-08-22 14:12:03.617124'),(30,'core','0013_invoice_invoiceitem','2025-08-22 14:12:04.326517'),(31,'core','0014_employee_can_view_attendance_and_more','2025-08-22 14:12:05.534567'),(32,'core','0015_attendance_system_updates','2025-08-22 14:12:07.518923'),(33,'core','0016_rename_core_attendance_employee_123456_idx_core_attend_employe_584fa1_idx_and_more','2025-08-22 14:12:07.850745'),(34,'core','0017_employee_last_pay_date_employee_pay_frequency_and_more','2025-08-22 14:12:09.083368'),(35,'core','0018_taxslab_payrollitem_category_payrollitem_end_date_and_more','2025-08-22 14:12:09.669113'),(36,'core','0019_monthlypayrollrun','2025-08-22 14:12:09.737170'),(37,'core','0020_advancerequest','2025-08-22 14:12:10.003828'),(38,'sessions','0001_initial','2025-08-22 14:12:10.065758');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('np0x6i89uscqr76txtk90poho3iu20po','.eJxVjMEOgjAQBf-lZ9PIdkuLR-9-A-myr4IaSCicjP9umnDQ68xk3qZP-zb2e8HaT2oupjGnXyZpeGKuQh9pvi92WOZtncTWxB622NuieF2P9m8wpjLWbfQdQwJpjoGcz4wEQM5g6jJx4pCdh8ApGlLXSogxMBTaBiYyny_y2DhJ:1upSWg:agELCKpJLoI1CfPgOqz8y-uBEFZnnMDeTBQwF8cOyxk','2025-09-05 14:13:54.268638');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-26  5:15:02
