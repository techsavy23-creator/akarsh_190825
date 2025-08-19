\c store_monitoring;

ALTER DATABASE store_monitoring OWNER TO store_user;
ALTER SCHEMA public OWNER TO store_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO store_user;
GRANT ALL ON SCHEMA public TO store_user;


