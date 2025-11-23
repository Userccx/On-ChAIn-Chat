// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ETHUserDataMarketplace {
    address public owner;
    
    struct DataListing {
        address user;
        string dataHash;
        uint256 price;  // 价格单位：wei
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
    event Withdrawn(address indexed to, uint256 amount);
    event RefundFailed(address indexed to, uint256 amount);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
        listingCounter = 1;
    }
    
    // 上架
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
    
    // 购买
    function purchaseAccess(uint256 _listingId) external payable {
        DataListing storage listing = listings[_listingId];
        
        require(listing.isActive, "Listing is not active");
        require(listing.user != msg.sender, "Cannot purchase your own data");
        require(!hasAccess[msg.sender][_listingId], "Already have access");
        require(msg.value >= listing.price, "Insufficient ETH amount");
        
        // 先转账给数据所有者（主要业务逻辑）
        (bool success, ) = payable(listing.user).call{value: listing.price}("");
        require(success, "ETH transfer failed");
        
        // 再处理找零（次要逻辑）
        if (msg.value > listing.price) {
            uint256 refund = msg.value - listing.price;
            (bool refundSuccess, ) = payable(msg.sender).call{value: refund}("");
            // 找零失败不应该影响主要业务，所以不require
            if (!refundSuccess) {
                // 可以记录日志，但不revert
                emit RefundFailed(msg.sender, refund);
            }
        }
        
        hasAccess[msg.sender][_listingId] = true;
        
        accessRecords[msg.sender].push(AccessRecord({
            enterprise: msg.sender,
            listingId: _listingId,
            purchasedAt: block.timestamp,
            isValid: true
        }));
        
        emit AccessPurchased(_listingId, msg.sender, listing.user, listing.price);
    }
    
    // 下架
    function removeListing(uint256 _listingId) external {
        DataListing storage listing = listings[_listingId];
        require(listing.user == msg.sender, "Not the data owner");
        require(listing.isActive, "Listing already inactive");
        
        listing.isActive = false;
        emit ListingRemoved(_listingId);
    }
    
    // 检查访问权限
    function checkAccess(address _enterprise, uint256 _listingId) external view returns (bool) {
        return hasAccess[_enterprise][_listingId] && listings[_listingId].isActive;
    }
    
    // 获取用户的所有数据列表
    function getUserListings(address _user) external view returns (uint256[] memory) {
        return userListings[_user];
    }
    
    // 获取所有活跃的数据列表
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
    
    // 获取企业的访问记录
    function getEnterpriseAccessRecords(address _enterprise) external view returns (AccessRecord[] memory) {
        return accessRecords[_enterprise];
    }
    
    // 获取列表详情
    function getListingDetails(uint256 _listingId) external view returns (DataListing memory) {
        return listings[_listingId];
    }
    
    // 提取合约中意外收到的ETH（安全措施）
    function withdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No ETH to withdraw");
        
        (bool success, ) = payable(owner).call{value: balance}("");
        require(success, "Withdrawal failed");
        
        emit Withdrawn(owner, balance);
    }
    
    // 接收ETH的回退函数
    receive() external payable {}
}