PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE quote (
	id INTEGER NOT NULL, 
	document_type VARCHAR(50) NOT NULL, 
	quote_name VARCHAR(100), 
	quote_date VARCHAR(50), 
	company_logo VARCHAR(100), 
	notes TEXT, 
	doc_number VARCHAR(50) NOT NULL, 
	created_at DATETIME, 
	po_name VARCHAR(100), 
	po_date VARCHAR(50), 
	payment_terms VARCHAR(100), 
	shipping_name VARCHAR(100), 
	shipping_address VARCHAR(200), 
	shipping_city_state_zip VARCHAR(100), 
	billing_name VARCHAR(100), 
	billing_address VARCHAR(200), 
	billing_city_state_zip VARCHAR(100), 
	supplier_name VARCHAR(100), 
	supplier_quote VARCHAR(100), 
	supplier_contact VARCHAR(100), 
	end_user_name VARCHAR(100), 
	end_user_po VARCHAR(100), 
	end_user_contact VARCHAR(100), 
	po_amount VARCHAR(50), 
	PRIMARY KEY (id), 
	UNIQUE (doc_number)
);
INSERT INTO quote VALUES(2,'quote','EVTQ-SUSE-MLS','2025-10-16',NULL,replace('A Purchase Order must be received by October 31, 2025, for the Incentive Bundle Discount to apply\n\nNet terms are 120 days and will be invoiced on 2/28/2026\n\nGoverning terms for these SUSE Enterprise subscriptions falls under original SUSE MLA Contract # M40696757, also known as contract indentifier #7123964 , #00029205\n\nExecutive Summary – Walmart SUSE Multi-Linux Support (MLS) Project\n\n      •	Scope: 1,000 SUSE MLS 1-VM 3-Year Support Licenses covering SUSE and RHEL systems\n\n      •	Investment: $1,009,500 total\n\n      •	Savings: 65.7% off list pricing (≈ $1.93 million total savings)\n\n      •	Term: 3 years (Nov 2025 – Oct 2028) + 4-month no-cost extension through Feb 2029\n\n      •	Included at No Cost (to reduce risk and ensure a successful project):\n\n          • Premium Gold Support – 24×7 enterprise coverage with dedicated Technical Account Manager\n\n	  • RHEL 7 Extended Lifecycle Support (LTSS) – Security updates and CVE patching beyond Red Hat EOL\n\n	  • SUSE Assist Consulting – 4 total weeks of embedded engineering support for onboarding and optimization\n\n       • Program Value:\n\n          • Unified Linux support model simplifies operations and consolidates vendor management\n\n	  • Extended lifecycle and proactive coverage enhance security and reduce operational risk\n\n	  • Pilot establishes a scalable, cost-efficient foundation for future enterprise rollout\n\n⸻\n\n','\n',char(10)),'EVTQ20250918182038','2025-09-18 18:20:38.038951',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO quote VALUES(3,'po',NULL,NULL,NULL,replace('Note: Ship to:\nRobbi Roughton\nEDC DOCK #3\n805 SE MOBERLY LN\nBENTONVILLE, AR 72712','\n',char(10)),'EVTPO20250919175556','2025-09-19 17:55:56.017994','EVTPO-PURE-FA100','2025-09-19','Net45','Walmart Inc.','805 E. Moberly Ln','Bentonville, AR 72712','Enterprise Vision Technologies','201 Wilshire Blvd, A-9','Santa Monica, CA 90401','Pure Storage','Q-1108741','Chip McCulley II (dmcculley@purestorage.com)','Walmart Inc.','6307756328','Daniel Ryberg (daniel.ryberg@walmart.com)','14500.80');
INSERT INTO quote VALUES(4,'quote','EVTQ-PURE-EDC','2025-10-13',NULL,'CR - 67194','EVTQ20251013163431','2025-10-13 16:34:31.505765',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO quote VALUES(5,'quote','EVTQ-PURE-NDC','2025-10-14',NULL,'CR - 67300','EVTQ20251013163432','2025-10-14 13:01:07.388011',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO quote VALUES(6,'quote','EVTQ-PURE-CDC','2025-10-14',NULL,'CR - 67302','EVTQ20251013163433','2025-10-14 13:01:17.435922',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO quote VALUES(7,'po',NULL,NULL,NULL,replace('Quote Number: Q-214292\nContract Number: 00029205','\n',char(10)),'EVTPO20251014184346','2025-10-14 18:43:46.060691','EVTPO-SUSE-MLS','2025-10-14','Net 120','Walmart, Inc.','805 SE Moberly Ln','Bentonville, AR 72716','Enterprise Vision Technologies','201 Wilshire Blvd, Suite A9','Santa Monica, CA 90401','SUSE','Q-214292','Daniel Thaure (daniel.thaure1@suse.com)','Walmart, Inc.',NULL,'Josh Russell (josh.russell@walmart.com)','836343.33');
CREATE TABLE line_item (
	id INTEGER NOT NULL, 
	quote_id INTEGER NOT NULL, 
	item_type VARCHAR(50) NOT NULL, 
	title VARCHAR(100), 
	part_number VARCHAR(100), 
	description TEXT, 
	item_category VARCHAR(100), 
	unit_price FLOAT, 
	quantity INTEGER, 
	discounted_price FLOAT, 
	extended_price FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(quote_id) REFERENCES quote (id)
);
INSERT INTO line_item VALUES(1859,5,'section','NDC - FB S500R2 1350TB (Hardware + Support)',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1860,5,'item',NULL,'FB-S500R2-1350TB-37DFMc','Pure Storage FlashBlade// S500 R2 system SKU using 37.5TB drive. 1350TB of raw storage capacity. Includes hardware and software license., 1 chassis, 9 blades, 4 drive/ blade.','Hardware',2618714.0,1,906931.5699999999487,906931.5699999999487);
INSERT INTO line_item VALUES(1861,5,'item',NULL,'FB-S500R2-1350TB-37DFMc, 1MO,PRM,FVR','FB-S500R2- 1350TB- 37DFMc 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',9150.0,36,7136.010000000000218,256896.3600000000151);
INSERT INTO line_item VALUES(1862,5,'section','NDC - FB S500R2 262TB (Hardware + Support)',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1863,5,'item',NULL,'FB-S200R2-262TB-37DFMc','Pure Storage FlashBlade// S200 R2 system SKU using 37.5TB drive. 262TB of raw storage capacity. Includes hardware and software license., 1 chassis, 7 blades, 1 drive/ blade.','Hardware',658114.0,1,197371.3399999999966,197371.3399999999966);
INSERT INTO line_item VALUES(1864,5,'item',NULL,'FB-S200R2-262TB-37DFMc, 1MO,PRM,FVR','FB-S200R2- 262TB- 37DFMc 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',3636.0,36,3104.829999999999928,111773.8800000000046);
INSERT INTO line_item VALUES(1865,5,'section','NDC - FB S500R2 1050TB (Hardware + Support)',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1866,5,'item',NULL,'FB-S500R2-1050TB-37DFMc','Pure Storage FlashBlade// S500 R2 system SKU using 37.5TB drive. 1050TB of raw storage capacity. Includes hardware and software license., 1 chassis, 7 blades, 4 drive/ blade.','Hardware',2121486.0,1,443186.1500000000232,443186.1500000000232);
INSERT INTO line_item VALUES(1867,5,'item',NULL,'FB-S500R2-1050TB-37DFMc, 1MO,PRM,FVR','FB-S500R2- 1050TB- 37DFMc 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',8259.0,36,6588.460000000000036,237184.5599999999977);
INSERT INTO line_item VALUES(1868,5,'section','NDC - FB S500R2 525TB (Hardware + Support)',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1869,5,'item',NULL,'FB-S500R2-525TB-37DFMc','Pure Storage FlashBlade// S500 R2 system SKU using 37.5TB drive. 525TB of raw storage capacity. Includes hardware and software license., 1 chassis, 7 blades, 2 drive/ blade.','Hardware',1261024.0,1,332879.6900000000023,332879.6900000000023);
INSERT INTO line_item VALUES(1870,5,'item',NULL,'FB-S500R2-525TB-37DFMc, 1MO,PRM,FVR','FB-S500R2- 525TB- 37DFMc 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',6368.0,36,5168.039999999999964,186049.4400000000023);
INSERT INTO line_item VALUES(1871,5,'section','Accessories + Expansion',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1872,5,'item',NULL,'FB-S-MC-Accessory-Kit-1M-Copper','FlashBlade//S Multi-Chassis Accessory Kit, 1M length, Copper','Hardware',5650.0,4,1709.220000000000027,6836.880000000000109);
INSERT INTO line_item VALUES(1873,5,'item',NULL,'FB-S-Accessory-Kit','FlashBlade//S 100G Cableand- optic Accessory Kit','Hardware',10000.0,4,3025.170000000000072,12100.68000000000029);
INSERT INTO line_item VALUES(1874,5,'item',NULL,'FB-MC-XFM-8400R2','FlashBlade External Fabric Modules (XFM-8400R2) for multichassis deployments (Quantity 2)','Hardware',140000.0,4,42352.37000000000262,169409.4800000000104);
INSERT INTO line_item VALUES(1875,5,'item',NULL,'FB-MC-XFM-8400R2, 1MO,PRM,FVR','FB-MC-XFM- 8400R2 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',675.0,144,510.5,73512.0);
INSERT INTO line_item VALUES(1876,5,'item',NULL,'FB-40Gb-Eth-SFP-SR (4 pack)','4 pack of 40Gb Ethernet Short Range QSFP28 Transceiver','Hardware',4400.0,3,1220.15000000000009,3660.450000000000273);
INSERT INTO line_item VALUES(1877,6,'section','CDC - FB S500R2 1350TB (Hardware + Support)',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1878,6,'item',NULL,'FB-S500R2-1350TB-37DFMc','Pure Storage FlashBlade// S500 R2 system SKU using 37.5TB drive. 1350TB of raw storage capacity. Includes hardware and software license., 1 chassis, 9 blades, 4 drive/ blade.','Hardware',2618714.0,2,906931.5699999999487,1813863.139999999898);
INSERT INTO line_item VALUES(1879,6,'item',NULL,'FB-S500R2-1350TB-37DFMc, 1MO,PRM,FVR','FB-S500R2- 1350TB- 37DFMc 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',9150.0,72,7136.010000000000218,513792.7200000000302);
INSERT INTO line_item VALUES(1880,6,'section','CDC - FB S500R2 525TB (Hardware + Support)',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1881,6,'item',NULL,'FB-S500R2-525TB-37DFMc','Pure Storage FlashBlade// S500 R2 system SKU using 37.5TB drive. 525TB of raw storage capacity. Includes hardware and software license., 1 chassis, 7 blades, 2 drive/ blade.','Hardware',1261024.0,1,332879.6900000000023,332879.6900000000023);
INSERT INTO line_item VALUES(1882,6,'item',NULL,'FB-S500R2-525TB-37DFMc, 1MO,PRM,FVR','FB-S500R2- 525TB- 37DFMc 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',6368.0,36,5168.039999999999964,186049.4400000000023);
INSERT INTO line_item VALUES(1883,6,'section','Accessories + Expansion',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1884,6,'item',NULL,'FB-S-MC-Accessory-Kit-1M-Copper','FlashBlade//S Multi-Chassis Accessory Kit, 1M length, Copper','Hardware',5650.0,3,1709.220000000000027,5127.659999999999855);
INSERT INTO line_item VALUES(1885,6,'item',NULL,'FB-S-Accessory-Kit','FlashBlade//S 100G Cableand- optic Accessory Kit','Hardware',10000.0,3,3025.170000000000072,9075.510000000000218);
INSERT INTO line_item VALUES(1886,6,'item',NULL,'FB-40Gb-Eth-SFP-SR (4 pack)','4 pack of 40Gb Ethernet Short Range QSFP28 Transceiver','Hardware',4400.0,6,1220.15000000000009,7320.900000000000546);
INSERT INTO line_item VALUES(1887,6,'item',NULL,'FB-MC-XFM-8400R2','FlashBlade External Fabric Modules (XFM-8400R2) for multichassis deployments (Quantity 2)','Hardware',140000.0,3,42352.37000000000262,127057.1100000000152);
INSERT INTO line_item VALUES(1888,6,'item',NULL,'FB-MC-XFM-8400R2, 1MO,PRM,FVR','FB-MC-XFM- 8400R2 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',675.0,108,510.5,55134.0);
INSERT INTO line_item VALUES(1889,4,'section','EDC - FB S500R2 1350TB (Hardware + Support)',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1890,4,'item',NULL,'FB-S500R2-1350TB-37DFMc','Pure Storage FlashBlade// S500 R2 system SKU using 37.5TB drive. 1350TB of raw storage capacity. Includes hardware and software license., 1 chassis, 9 blades, 4 drive/ blade.','Hardware',2618714.0,1,906931.5699999999487,906931.5699999999487);
INSERT INTO line_item VALUES(1891,4,'item',NULL,'FB-S500R2-1350TB-37DFMc, 1MO,PRM,FVR','FB-S500R2- 1350TB- 37DFMc 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',9150.0,36,7136.010000000000218,256896.3600000000151);
INSERT INTO line_item VALUES(1892,4,'section','PCNA - FB S200SR 262TB (Hardware + Support) ',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1893,4,'item',NULL,'FB-S200R2-262TB-37DFMc','Pure Storage FlashBlade// S200 R2 system SKU using 37.5TB drive. 262TB of raw storage capacity. Includes hardware and software license., 1 chassis, 7 blades, 1 drive/ blade.','Hardware',658114.0,1,197371.3399999999966,197371.3399999999966);
INSERT INTO line_item VALUES(1894,4,'item',NULL,'FB-S200R2-262TB-37DFMc, 1MO,PRM,FVR','FB-S200R2- 262TB- 37DFMc 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',3636.0,36,3104.829999999999928,111773.8800000000046);
INSERT INTO line_item VALUES(1895,4,'section','EDC - FB S500R2 1050TB (Hardware + Support)',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1896,4,'item',NULL,'FB-S500R2-1050TB-37DFMc','Pure Storage FlashBlade// S500 R2 system SKU using 37.5TB drive. 1050TB of raw storage capacity. Includes hardware and software license., 1 chassis, 7 blades, 4 drive/ blade.','Hardware',2121486.0,1,443186.1500000000232,443186.1500000000232);
INSERT INTO line_item VALUES(1897,4,'item',NULL,'FB-S500R2-1050TB-37DFMc, 1MO,PRM,FVR','FB-S500R2- 1050TB- 37DFMc 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',8259.0,36,6588.460000000000036,237184.5599999999977);
INSERT INTO line_item VALUES(1898,4,'section','EDC - FB S500R2 525TB (Hardware + Support)',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1899,4,'item',NULL,'FB-S500R2-525TB-37DFMc','Pure Storage FlashBlade// S500 R2 system SKU using 37.5TB drive. 525TB of raw storage capacity. Includes hardware and software license., 1 chassis, 7 blades, 2 drive/ blade.','Hardware',1261024.0,3,332879.6900000000023,998639.070000000066);
INSERT INTO line_item VALUES(1900,4,'item',NULL,'FB-S500R2-525TB-37DFMc, 1MO,PRM,FVR','FB-S500R2- 525TB- 37DFMc 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',6368.0,108,5168.039999999999964,558148.3199999999487);
INSERT INTO line_item VALUES(1901,4,'section','Accessories + Expansion',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(1902,4,'item',NULL,'FB-S-MC-Accessory-Kit-1M-Copper','FlashBlade//S Multi-Chassis Accessory Kit, 1M length, Copper','Hardware',5650.0,6,1709.220000000000027,10255.31999999999971);
INSERT INTO line_item VALUES(1903,4,'item',NULL,'FB-S-Accessory-Kit','FlashBlade//S 100G Cableand- optic Accessory Kit','Hardware',10000.0,6,3025.170000000000072,18151.02000000000043);
INSERT INTO line_item VALUES(1904,4,'item',NULL,'FB-MC-XFM-8400R2','FlashBlade External Fabric Modules (XFM-8400R2) for multichassis deployments (Quantity 2)','Hardware',140000.0,6,42352.37000000000262,254114.2200000000303);
INSERT INTO line_item VALUES(1905,4,'item',NULL,'FB-MC-XFM-8400R2, 1MO,PRM,FVR','FB-MC-XFM- 8400R2 1 Month Evergreen Forever Subscription, 4 Hour Delivery, 24/7 Support','Support',675.0,216,510.5,110268.0);
INSERT INTO line_item VALUES(1906,4,'item',NULL,'FB-40Gb-Eth-SFP-SR (4 pack)','4 pack of 40Gb Ethernet Short Range QSFP28 Transceiver','Hardware',4400.0,3,1220.15000000000009,3660.450000000000273);
INSERT INTO line_item VALUES(2042,2,'section','Support Subscription',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(2043,2,'item',NULL,'EVT-SMLS-1VM-3YR','SMLS X86-64 1 VM PR 3YR - SUSE Multi-Linux Support','Support',1799.0,1000,1009.5,1009500.0);
INSERT INTO line_item VALUES(2044,2,'item',NULL,'EVT-SMLS-1VM-4MO','SMLS X86-64 1 VM PR 3YR - SUSE Multi-Linux Support','Support',200.0,1000,0.0,0.0);
INSERT INTO line_item VALUES(2045,2,'item',NULL,'EVT-RHEL7-LTSS-1YR','RHEL 7 LTSS -ULM- 1YR Extended Lifecycle Support for RHEL 7','Support',150000.0,3,0.0,0.0);
INSERT INTO line_item VALUES(2046,2,'item',NULL,'EVT-RHEL7-LTSS-4MO','RHEL 7 LTSS -ULM- 1YR Extended Lifecycle Support for RHEL 7','Support',50000.0,1,0.0,0.0);
INSERT INTO line_item VALUES(2047,2,'section','Premium Services and Consulting',NULL,NULL,NULL,0.0,0,0.0,0.0);
INSERT INTO line_item VALUES(2048,2,'item',NULL,'EVT-SMLS-GOLD-1YR','SUSE PREMIUM GOLD - US - 1YR Technical Account Management','Services',133000.0,3,0.0,0.0);
INSERT INTO line_item VALUES(2049,2,'item',NULL,'EVT-SMLS-GOLD-4MO','SUSE PREMIUM GOLD - US - 4MO Technical Account Management','Services',44333.33000000000174,1,0.0,0.0);
INSERT INTO line_item VALUES(2050,2,'item',NULL,'EVT-SUSE-ASSIST-1WK','SUSE Assist - 1 Week (up to 40 hrs) - US Consulting Services','Services',13750.0,4,0.0,0.0);
CREATE TABLE subcomponent (
	id INTEGER NOT NULL, 
	line_item_id INTEGER NOT NULL, 
	description VARCHAR(200) NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(line_item_id) REFERENCES line_item (id)
);
INSERT INTO subcomponent VALUES(1,2043,'Term in months (11/01/25 - 10/31/28)',40);
INSERT INTO subcomponent VALUES(2,2044,'Term in months (11/01/28 - 02/28/29)',1);
INSERT INTO subcomponent VALUES(3,2045,'Term in months (11/01/25 - 10/31/28)',36);
INSERT INTO subcomponent VALUES(4,2046,'Term in months (11/01/28 - 02/28/29)',4);
INSERT INTO subcomponent VALUES(5,2048,'Term in months (11/01/25 - 10/31/28)',36);
INSERT INTO subcomponent VALUES(6,2049,'Term in months (11/01/28 - 02/28/29)',4);
COMMIT;
