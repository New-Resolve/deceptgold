// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DeceptGoldToken is ERC20, Ownable {
    address public validatorContract;

    constructor(address initialOwner) ERC20("DECEPTGOLD", "DGLD") Ownable(initialOwner) {}

    function setValidatorContract(address _validator) external onlyOwner {
        validatorContract = _validator;
    }

    function mint(address to, uint256 amount) external {
        require(msg.sender == validatorContract, "Only validator can mint");
        _mint(to, amount);
    }

    function decimals() public pure override returns (uint8) {
        return 4;
    }
}
