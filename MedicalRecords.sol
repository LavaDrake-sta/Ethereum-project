// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MedicalRecords {

    address public admin;

    struct Doctor {
        string doctorId;
        string username;
        bytes32 passwordHash; // שמירת הסיסמא כהאש מוצפן
        string specialty;
        bool isAuthorized;
    }

    struct Patient {
        string name;
        uint256 age;
        string addressPatient;
        string hmo;
    }

    struct Record {
        string patientId;
        string doctorId;
        string treatmentDetails;
        uint256 timestamp;
    }

    mapping(address => Doctor) public doctors; // מיפוי כתובת לרופא
    mapping(string => address) public usernameToAddress; // מיפוי שם משתמש לכתובת רופא
    mapping(string => Patient) public patients; // מיפוי של תעודת זהות של המטופל לפרטי המטופל
    mapping(string => Record[]) public records; // מיפוי של תעודת זהות של המטופל לרשומות שלו

    constructor() {
        admin = msg.sender;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action.");
        _;
    }

    modifier onlyAuthorizedDoctor() {
        require(doctors[msg.sender].isAuthorized, "Only authorized doctors can perform this action.");
        _;
    }

    function addDoctor(
        address doctorAddress, 
        string memory _doctorId, 
        string memory _username, 
        string memory _password, 
        string memory _specialty
    ) public onlyAdmin {
        bytes32 passwordHash = keccak256(abi.encodePacked(_password));

        doctors[doctorAddress] = Doctor({
            doctorId: _doctorId,
            username: _username,
            passwordHash: passwordHash,
            specialty: _specialty,
            isAuthorized: true
        });

        // שמירת המיפוי בין שם המשתמש לכתובת הרופא
        usernameToAddress[_username] = doctorAddress;
    }

    function authenticateDoctor(
        string memory _username, 
        string memory _password
    ) public view returns (bool) {
        address doctorAddress = usernameToAddress[_username];
        require(doctorAddress != address(0), "Doctor not found.");

        bytes32 passwordHash = keccak256(abi.encodePacked(_password));
        return doctors[doctorAddress].passwordHash == passwordHash;
    }

    function addPatient(
        string memory _patientId, 
        string memory _name, 
        uint256 _age, 
        string memory _addressPatient, 
        string memory _hmo
    ) public onlyAuthorizedDoctor {
        patients[_patientId] = Patient(_name, _age, _addressPatient, _hmo);
    }

    function getPatient(string memory _patientId) 
        public view returns (string memory, uint256, string memory, string memory) 
    {
        Patient memory patient = patients[_patientId];
        return (patient.name, patient.age, patient.addressPatient, patient.hmo);
    }

    function addRecord(
        string memory _patientId, 
        string memory _doctorId, 
        string memory _treatmentDetails
    ) public onlyAuthorizedDoctor {
        require(bytes(patients[_patientId].name).length != 0, "Patient does not exist.");

        records[_patientId].push(Record({
            patientId: _patientId,
            doctorId: _doctorId,
            treatmentDetails: _treatmentDetails,
            timestamp: block.timestamp
        }));
    }

    function getRecords(string memory _patientId) public view returns (Record[] memory) {
        return records[_patientId];
    }

    function getDoctor(address doctorAddress) 
        public view returns (string memory, string memory, bool) 
    {
        Doctor memory doctor = doctors[doctorAddress];
        return (doctor.username, doctor.specialty, doctor.isAuthorized);
    }
}