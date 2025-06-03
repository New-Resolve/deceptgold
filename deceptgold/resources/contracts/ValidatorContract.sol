// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./DeceptGoldToken.sol";

contract ValidatorContract {
    address public constant EXPECTED_SIGNER = 0xfA6a145a7e1eF7367888A39CBf68269625C489D2;
    mapping(bytes32 => bool) public usedHashes;

    DeceptGoldToken public token;

    event SignerRecovered(address signer);

    constructor(address tokenAddress) {
        token = DeceptGoldToken(tokenAddress);
    }

    function claimToken(
        bytes32 jsonHash,
        bytes memory signature,
        address recipient
    ) external {
        bytes32 ethSignedHash = prefixed(jsonHash);
        address signer = recoverSigner(ethSignedHash, signature);

        emit SignerRecovered(signer);

        require(signer == EXPECTED_SIGNER, "Invalid signer");
        usedHashes[jsonHash] = true;

        token.mint(recipient, 1);
    }

    function recoverSigner(bytes32 ethSignedMessageHash, bytes memory sig)
        public pure returns (address)
    {
        require(sig.length == 65, "Invalid signature length");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }

        return ecrecover(ethSignedMessageHash, v, r, s);
    }

    function prefixed(bytes32 hash) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", hash));
    }
}
