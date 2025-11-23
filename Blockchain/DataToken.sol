// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/ERC20.sol";

contract DataToken is ERC20 {
    constructor(uint256 initialSupply) ERC20("DataToken", "DTK") {
        _mint(msg.sender, initialSupply * 10**decimals());
    }
    
    // 铸币函数
    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}