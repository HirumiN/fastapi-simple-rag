# TODO: Add Database Features for Management App

## 1. Add Models in models.py
- [x] Add Todo model with fields: id_todo, id_user (FK), nama, tipe, tenggat, deskripsi
- [x] Add JadwalMatkul model with fields: id_jadwal, id_user (FK), hari, nama, jam_mulai, jam_selesai, sks
- [x] Add UKM model with fields: id_ukm, id_user (FK), nama, jabatan, deskripsi

## 2. Add Schemas in schemas.py
- [x] Add Pydantic schemas for Todo (Base, Create, Response)
- [x] Add Pydantic schemas for JadwalMatkul (Base, Create, Response)
- [x] Add Pydantic schemas for UKM (Base, Create, Response)

## 3. Add CRUD Operations in crud.py
- [x] Add CRUD functions for Todo: create, read, update, delete
- [x] Add CRUD functions for JadwalMatkul: create, read, update, delete
- [x] Add CRUD functions for UKM: create, read, update, delete

## 4. Add API Endpoints in main.py
- [ ] Add endpoints for Todo management (GET, POST, PUT, DELETE)
- [ ] Add endpoints for JadwalMatkul management (GET, POST, PUT, DELETE)
- [ ] Add endpoints for UKM management (GET, POST, PUT, DELETE)

## 5. Update HTML Template (index.html)
- [x] Add sections to display and manage Todos
- [x] Add sections to display and manage JadwalMatkul
- [x] Add sections to display and manage UKM
- [x] Add forms for creating new entries
- [x] Add JavaScript for dynamic interactions

## 6. Testing and Verification
- [ ] Test database table creation
- [ ] Test API endpoints
- [ ] Verify frontend integration

## 7. Error Checking and Fixes
- [ ] Add CRUD functions for Todo in crud.py
- [ ] Add CRUD functions for JadwalMatkul in crud.py
- [ ] Add CRUD functions for UKM in crud.py
- [ ] Run tests to check for errors
