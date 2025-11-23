// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// ERC20接口
interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function allowance(address owner, address spender) external view returns (uint256);
}

contract UserDataMarketplace {
    IERC20 public paymentToken;
    address public owner;
    
    // 重入保护
    bool private locked;
    
    struct DataListing {
        address user;
        string dataHash;
        uint256 price;
        bool isActive;
        uint256 createdAt;
    }
    
    struct AccessRecord {
        address enterprise;
        uint256 listingId;
        uint256 purchasedAt;
        bool isValid;
    }
    
    mapping(uint256 => DataListing) public listings;
    mapping(address => uint256[]) public userListings;
    mapping(address => mapping(uint256 => bool)) public hasAccess;
    mapping(address => AccessRecord[]) public accessRecords;
    
    uint256 private listingCounter;
    
    event DataListed(uint256 indexed listingId, address indexed user, string dataHash, uint256 price);
    event AccessPurchased(uint256 indexed listingId, address indexed enterprise, address indexed user, uint256 price);
    event ListingRemoved(uint256 indexed listingId);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    modifier nonReentrant() {
        require(!locked, "No reentrancy");
        locked = true;
        _;
        locked = false;
    }
    
    constructor(address _paymentToken) {
        paymentToken = IERC20(_paymentToken);
        owner = msg.sender;
        listingCounter = 1;
    }
    
    function listData(string memory _dataHash, uint256 _price) external returns (uint256) {
        require(_price > 0, "Price must be greater than 0");
        require(bytes(_dataHash).length > 0, "Data hash cannot be empty");
        
        uint256 listingId = listingCounter;
        listings[listingId] = DataListing({
            user: msg.sender,
            dataHash: _dataHash,
            price: _price,
            isActive: true,
            createdAt: block.timestamp
        });
        
        userListings[msg.sender].push(listingId);
        listingCounter++;
        
        emit DataListed(listingId, msg.sender, _dataHash, _price);
        return listingId;
    }
    
    function purchaseAccess(uint256 _listingId) external nonReentrant {
        DataListing storage listing = listings[_listingId];
        
        require(listing.isActive, "Listing is not active");
        require(listing.user != msg.sender, "Cannot purchase your own data");
        require(!hasAccess[msg.sender][_listingId], "Already have access");
        
        uint256 price = listing.price;
        require(paymentToken.balanceOf(msg.sender) >= price, "Insufficient token balance");
        require(paymentToken.allowance(msg.sender, address(this)) >= price, "Insufficient token allowance");
        
        bool success = paymentToken.transferFrom(msg.sender, listing.user, price);
        require(success, "Token transfer failed");
        
        hasAccess[msg.sender][_listingId] = true;
        
        accessRecords[msg.sender].push(AccessRecord({
            enterprise: msg.sender,
            listingId: _listingId,
            purchasedAt: block.timestamp,
            isValid: true
        }));
        
        emit AccessPurchased(_listingId, msg.sender, listing.user, price);
    }
    
    function removeListing(uint256 _listingId) external {
        DataListing storage listing = listings[_listingId];
        require(listing.user == msg.sender, "Not the data owner");
        require(listing.isActive, "Listing already inactive");
        
        listing.isActive = false;
        emit ListingRemoved(_listingId);
    }
    
    function checkAccess(address _enterprise, uint256 _listingId) external view returns (bool) {
        return hasAccess[_enterprise][_listingId] && listings[_listingId].isActive;
    }
    
    function getUserListings(address _user) external view returns (uint256[] memory) {
        return userListings[_user];
    }
    
    function getActiveListings() external view returns (uint256[] memory) {
        uint256 activeCount = 0;
        
        for (uint256 i = 1; i < listingCounter; i++) {
            if (listings[i].isActive) {
                activeCount++;
            }
        }
        
        uint256[] memory activeListings = new uint256[](activeCount);
        uint256 currentIndex = 0;
        
        for (uint256 i = 1; i < listingCounter; i++) {
            if (listings[i].isActive) {
                activeListings[currentIndex] = i;
                currentIndex++;
            }
        }
        
        return activeListings;
    }
    
    function getEnterpriseAccessRecords(address _enterprise) external view returns (AccessRecord[] memory) {
        return accessRecords[_enterprise];
    }
    
    function getListingDetails(uint256 _listingId) external view returns (DataListing memory) {
        return listings[_listingId];
    }
    
    // recover（废弃）
    function recoverToken(address tokenAddress, uint256 amount) external onlyOwner {
        IERC20(tokenAddress).transfer(owner, amount);
    }
}