/**
    Transaction to create a new Election resource and save it into a storage path provided as argument, as well as publishing a capability to the public path provided as well.

    @param _electionName (String) The name of the Election resource.
    @param _electionBallot (String) The question that this Election wants to answer.
    @param _electionOptions ({UInt8: String}) The set of Ballot voting options that the voter must chose from. For easier processing, these should be arranged in a UInt8: <OptionText> format for frontend consumption.
    @param _publicKey (String) The public encryption key String. This key is to be used by the frontend to encrypt any options for Ballots submitted to this Election.
    @param _electionStoragePath (StoragePath) A storage path-type element indicating where, in the contract deployer's account, the Election resource should be storage into.
    @param _electionPublicPath (PublicPath) A public path-type element indicating where, in the contract deployer's account, the public interface of the Election resource should be published into.
**/

import VoteBooth from 0x287f5c8b0865c516
import ElectionStandard from 0x287f5c8b0865c516

transaction(
    _electionName: String, 
    _electionBallot: String, 
    _electionOptions: {UInt8: String},
    _publicKey: String,
    _electionStoragePath: StoragePath,
    _electionPublicPath: PublicPath
    ) {
    let voteBoothPrinterAdminRef: &VoteBooth.VoteBoothPrinterAdmin
    let newElectionId: UInt64

    prepare(signer: auth(Storage, Capabilities, ElectionStandard.ElectionAdmin) &Account) {
        // Get the authorized reference for the VoteBoothPrinterAdmin resource with all the entitlements specified in the transaction signature
        self.voteBoothPrinterAdminRef 
            = signer.storage.borrow<auth(Storage, Capabilities, ElectionStandard.ElectionAdmin) &VoteBooth.VoteBoothPrinterAdmin>(from: VoteBooth.voteBoothPrinterAdminStoragePath) ??
            panic(
                "Unable to retrieve a valid auth(Storage, Capabilities, ElectionStandard.ElectionAdmin) &VoteBooth.VoteBoothPrinterAdmin at `VoteBooth.voteBoothPrinterAdminStoragePath.toString()` from account at `signer.address.toString()`"
            )
        
        // Create the Election in this prepare phase because I need access to the signer variable.
        self.newElectionId = self.voteBoothPrinterAdminRef.createElection(
            newElectionName: _electionName,
            newElectionBallot: _electionBallot,
            newElectionOptions: _electionOptions,
            newPublicKey: _publicKey,
            newElectionStoragePath: _electionStoragePath,
            newElectionPublicPath: _electionPublicPath,
            deployerAccount: signer
        )
    }

    execute {}
}