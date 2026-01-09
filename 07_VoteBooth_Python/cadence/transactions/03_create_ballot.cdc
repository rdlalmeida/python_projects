/**
    Transaction to create a new Ballot into a VoteBox resource into a voter account passed as input argument.

    @param _linkedElectionId (UInt64) The electionId that the Ballot to create is associated to.
    @param _voterAddress (Address) The account address of the voter account where this Ballot is to be stored into.
**/

import ElectionStandard from 0xf8d6e0586b0a20c7
import VoteBoxStandard from 0xf8d6e0586b0a20c7
import VoteBooth from 0xf8d6e0586b0a20c7

transaction(_linkedElectionId: UInt64, _voterAddress: Address) {
    let voteBoothPrinterAdminRef: &VoteBooth.VoteBoothPrinterAdmin

    prepare(signer: auth(BorrowValue, VoteBoxStandard.VoteBoxAdmin, ElectionStandard.ElectionAdmin) &Account) {
        // Grab an authorized reference to the VoteBoothPrinterAdmin resource using the signer account
        self.voteBoothPrinterAdminRef = signer.storage.borrow<&VoteBooth.VoteBoothPrinterAdmin>(from: VoteBooth.voteBoothPrinterAdminStoragePath) ??
        panic(
            "Unable to retrieve a valid &VoteBooth.VoteBoothPrinterAdmin at `VoteBooth.voteBoothPrinterAdminStoragePath.toString()` for account `signer.address.toString()`"
        )

        let newBallotId: UInt64 = self.voteBoothPrinterAdminRef.createBallot(newLinkedElectionId: _linkedElectionId, voterAddress: _voterAddress, deployer: signer) ??
        panic(
            "Unable to create a Ballot for Election `_linkedElectionId.toString()` and deposit it to voter account at `_voterAddress.toString()` using the VoteBoothPrinterAdmin at `VoteBooth.voteBoothPrinterAdminStoragePath.toString()` from account `signer.address.toString()`"
        )

        if (VoteBooth.verbose) {
            log(
                "Successfully created Ballot with id `newBallotId.toString()` and deposited to the VoteBox in account `_voterAddress.toString()`"
                )
        }
    }

    execute {
    }
}